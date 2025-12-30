// Three.js Holo-Globe Implementation
let scene, camera, renderer, globe;

function init() {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

    renderer = new THREE.WebGLRenderer({
        canvas: document.querySelector('#globe-canvas'),
        alpha: true,
        antialias: true
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    // Create Globe
    const geometry = new THREE.IcosahedronGeometry(1.5, 12); // Detailed sphere

    // Wireframe Material
    const material = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        wireframe: true,
        transparent: true,
        opacity: 0.15
    });

    globe = new THREE.Mesh(geometry, material);
    scene.add(globe);

    // Add Points (Holo effect)
    const pointsGeometry = new THREE.IcosahedronGeometry(1.51, 15);
    const pointsMaterial = new THREE.PointsMaterial({
        color: 0x00f0ff,
        size: 0.02,
        transparent: true,
        opacity: 0.6
    });
    const points = new THREE.Points(pointsGeometry, pointsMaterial);
    globe.add(points);

    camera.position.z = 4;

    animate();
}

function animate() {
    requestAnimationFrame(animate);

    globe.rotation.y += 0.002;
    globe.rotation.x += 0.0005;

    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

init();
console.log("Holo-Globe Initialized.");
