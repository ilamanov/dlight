// Uncomment for debugging
// require.undef('sprite_visualizer');

// https://douglasduhaime.com/posts/visualizing-tsne-maps-with-three-js.html
define("sprite_visualizer", ["THREE"], function (THREE) {
  return (container, data) => {
    /** data should contain the following:
     * {
     *   embedding: ([list of tuples (x, y, z)]),
     *   atlas: {
     *     path: str,
     *     shape: {rows: int, cols: int},
     *     num_sprites: int,
     *     sprite_size: {height: int, width: int}
     *   },
     *   sprite_size_in_3D: {height: float, width: float},
     *   initial_camera_z: float
     * }
     */
    const { embedding, atlas, sprite_size_in_3D, initial_camera_z } = data;
    atlas.height = atlas.shape.rows * atlas.sprite_size.height;
    atlas.width = atlas.shape.cols * atlas.sprite_size.width;

    const canvas_width = Math.floor(1.0 * container.offsetWidth);
    const canvas_height = Math.floor(0.6 * canvas_width);

    const scene = new THREE.Scene();
    var mesh;

    var fieldOfView = 75;
    var aspectRatio = canvas_width / canvas_height;
    var nearPlane = 0.1;
    var farPlane = 20 * initial_camera_z;
    var camera = new THREE.PerspectiveCamera(
      fieldOfView,
      aspectRatio,
      nearPlane,
      farPlane
    );
    camera.position.z = initial_camera_z;

    // Create the canvas with a renderer and tell the
    // renderer to clean up jagged aliased lines
    var renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(canvas_width, canvas_height);

    // Add the canvas to the DOM
    container.appendChild(renderer.domElement);

    // Create a texture loader so we can load the
    // atlas image file into a custom material
    var loader = new THREE.TextureLoader();
    var material = new THREE.MeshBasicMaterial({
      map: loader.load(atlas.path),
    });

    // Add four vertices (one for each corner), in the following order:
    // lower left, lower right, upper right, upper left.
    // Assumes quads are facing -z axis.
    // Return index of the first vertex of this quad in geom.vertices
    function addQuad(geom, x, y, z, height, width) {
      let dx = width / 2.0;
      let dy = height / 2.0;
      geom.vertices.push(
        new THREE.Vector3(x - dx, y - dy, z),
        new THREE.Vector3(x + dx, y - dy, z),
        new THREE.Vector3(x + dx, y + dy, z),
        new THREE.Vector3(x - dx, y + dy, z)
      );
      return geom.vertices.length - 4;
    }

    // Add two faces for the quad.
    // Assumes that the vertices have been added to geom,
    // using the order specified in addQuad.
    // Assumes quads are facing -z axis.
    function addQuadFaces(geom, vtx1_idx) {
      geom.faces.push(
        // the lower-right triangle
        new THREE.Face3(vtx1_idx, vtx1_idx + 1, vtx1_idx + 2),
        // the upper-left triangle
        new THREE.Face3(vtx1_idx, vtx1_idx + 2, vtx1_idx + 3)
      );

      // // compute orientation of quad
      // let v1 = geom.vertices[vtx1_idx+1].clone().sub(geom.vertices[vtx1_idx]);
      // let v2 = geom.vertices[vtx1_idx+2].clone().sub(geom.vertices[vtx1_idx+1]);
      // v1.cross(v2);
      // v1.normalize();
      // return v1;
    }

    // Add UV coordinates for each vertex of last two faces
    function addQuadUVs(geom, u_left, u_right, v_top, v_bottom) {
      geom.faceVertexUvs[0].push([
        new THREE.Vector2(u_left, v_bottom),
        new THREE.Vector2(u_right, v_bottom),
        new THREE.Vector2(u_right, v_top),
      ]);
      geom.faceVertexUvs[0].push([
        new THREE.Vector2(u_left, v_bottom),
        new THREE.Vector2(u_right, v_top),
        new THREE.Vector2(u_left, v_top),
      ]);
    }

    // Create the empty geometry
    const geometry = new THREE.Geometry();

    // For each sprite in atlas,
    for (let y = 0; y < atlas.shape.rows; y++) {
      for (let x = 0; x < atlas.shape.cols; x++) {
        const sprite_idx = y * atlas.shape.cols + x;
        if (sprite_idx < atlas.num_sprites) {
          const vtx1_idx = addQuad(
            geometry,
            embedding[sprite_idx][0],
            embedding[sprite_idx][1],
            embedding[sprite_idx][2],
            sprite_size_in_3D.height,
            sprite_size_in_3D.width
          );

          addQuadFaces(geometry, vtx1_idx);

          const u_left = (x * atlas.sprite_size.width) / atlas.width;
          const u_right = u_left + 1.0 / atlas.shape.cols;

          const v_top = 1.0 - (y * atlas.sprite_size.height) / atlas.height;
          const v_bottom = v_top - 1.0 / atlas.shape.rows;

          addQuadUVs(geometry, u_left, u_right, v_top, v_bottom);
        }
      }
    }

    // // Rotate an object around an arbitrary axis in world space
    // // https://stackoverflow.com/a/11060965
    // function rotateAroundWorldAxis(object, rotWorldMatrix) {
    //     // old code for Three.JS pre r54:
    //     //  rotWorldMatrix.multiply(object.matrix);
    //     // new code for Three.JS r55+:
    //     rotWorldMatrix.multiply(object.matrix);                // pre-multiply

    //     object.matrix = rotWorldMatrix;

    //     // old code for Three.js pre r49:
    //     // object.rotation.getRotationFromMatrix(object.matrix, object.scale);
    //     // old code for Three.js pre r59:
    //     // object.rotation.setEulerFromRotationMatrix(object.matrix);
    //     // code for r59+:
    //     object.rotation.setFromRotationMatrix(object.matrix);
    // }

    // Always orient quads toward the camera
    function updateQuadOrientation() {
      // ----------------- Method1 (orthographic projection) ---------------------
      let new_orientation = new THREE.Vector3();
      camera.getWorldDirection(new_orientation);
      new_orientation.multiplyScalar(-1);
      new_orientation.normalize();
      let x_dir = camera.up.clone().cross(new_orientation).normalize();
      let y_dir = new_orientation.clone().cross(x_dir);

      let dw = x_dir.clone().multiplyScalar(sprite_size_in_3D.width / 2.0);
      let dh = y_dir.clone().multiplyScalar(sprite_size_in_3D.height / 2.0);
      // -------------------------------------------------------------------------

      for (let sprite_idx = 0; sprite_idx < atlas.num_sprites; sprite_idx++) {
        let sprite_vtx1_idx = sprite_idx * 4;

        let quad_pos = new THREE.Vector3(
          embedding[sprite_idx][0],
          embedding[sprite_idx][1],
          embedding[sprite_idx][2]
        );

        // ----------------- Method2 (perspective projection) ---------------------
        // let new_orientation = camera.position.clone().sub(quad_pos);
        // new_orientation.normalize();
        // let x_dir = camera.up.clone().cross(new_orientation).normalize();
        // let y_dir = new_orientation.clone().cross(x_dir);

        // let dw = x_dir.clone().multiplyScalar(sprite_size_in_3D.width / 2.0);
        // let dh = y_dir.clone().multiplyScalar(sprite_size_in_3D.height / 2.0);
        // -------------------------------------------------------------------------

        mesh.geometry.vertices[sprite_vtx1_idx + 0].copy(
          quad_pos.clone().sub(dw).sub(dh)
        );
        mesh.geometry.vertices[sprite_vtx1_idx + 1].copy(
          quad_pos.clone().add(dw).sub(dh)
        );
        mesh.geometry.vertices[sprite_vtx1_idx + 2].copy(
          quad_pos.clone().add(dw).add(dh)
        );
        mesh.geometry.vertices[sprite_vtx1_idx + 3].copy(
          quad_pos.clone().sub(dw).add(dh)
        );
      }
      mesh.geometry.verticesNeedUpdate = true;
    }

    // Combine the image geometry and material into a mesh
    mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(0, 0, 0);
    scene.add(mesh);

    // Add controls
    var controls = new THREE.TrackballControls(camera, renderer.domElement);
    controls.rotateSpeed = 1.0;
    controls.zoomSpeed = 2.0;
    controls.panSpeed = 0.8;

    controls.noZoom = false;
    controls.noPan = false;

    controls.staticMoving = false;
    controls.dynamicDampingFactor = 0.2;

    controls.keys = [65, 83, 68];
    // controls.addEventListener( 'change', updateQuadOrientation );
    controls.addEventListener("change", render);

    var axisHelper = new THREE.AxesHelper(
      /*size of arrows*/ sprite_size_in_3D.width
    );
    scene.add(axisHelper);

    // Handle window resizes
    container.addEventListener(
      "resize",
      function () {
        camera.aspect = container.innerWidth / container.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.innerWidth, container.innerHeight);
        controls.handleResize();
        render();
      },
      false
    );

    function render() {
      updateQuadOrientation();
      renderer.render(scene, camera);
      // mesh.lookAt(camera.position);
    }

    // The main animation function
    function animate() {
      controls.update();
      // render()
      requestAnimationFrame(animate);
    }
    animate();
    setTimeout(render, 100);
  };
});
