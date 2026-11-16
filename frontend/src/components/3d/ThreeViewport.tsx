import { useEffect, useRef } from "react";
import * as THREE from "three";

export function ThreeViewport({ preset, cameraMotion }: { preset: string; cameraMotion: string }) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#090B12");
    const camera = new THREE.PerspectiveCamera(45, (container.clientWidth || 600) / 280, 0.1, 100);
    camera.position.set(0, 1.8, 5.2);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth || 600, 280);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const point = new THREE.PointLight(0x8b5cf6, 40, 20);
    point.position.set(3, 4, 4);
    scene.add(point, new THREE.GridHelper(12, 12, 0x3b82f6, 0x1e293b));

    const geometry =
      preset === "orbit_logo" ? new THREE.TorusKnotGeometry(0.9, 0.28, 120, 16)
      : preset === "abstract_tech" ? new THREE.OctahedronGeometry(1.2, 1)
      : new THREE.IcosahedronGeometry(1.1, 2);
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0x8b5cf6, metalness: 0.75, roughness: 0.22 }));
    mesh.position.y = 1.2;
    scene.add(mesh);

    let frameId = 0;
    let t = 0;
    const animate = () => {
      t += 0.012;
      mesh.rotation.y += 0.01;
      if (cameraMotion === "orbit") {
        camera.position.x = Math.sin(t) * 5;
        camera.position.z = Math.cos(t) * 5;
        camera.lookAt(0, 1, 0);
      } else if (cameraMotion === "dolly_in") {
        camera.position.z = 5.5 - (Math.sin(t) + 1) * 1.1;
      } else {
        camera.position.x = Math.sin(t) * 2.2;
      }
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();
    return () => { cancelAnimationFrame(frameId); renderer.dispose(); };
  }, [preset, cameraMotion]);

  return <div ref={containerRef} className="w-full overflow-hidden rounded-lg border border-white/10" />;
}
