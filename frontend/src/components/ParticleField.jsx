import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

function Particles({ count = 1800 }) {
  const mesh = useRef();
  const light = useRef();

  const [positions, colors] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);
    const green = new THREE.Color("#00ff88");
    const blue  = new THREE.Color("#00d4ff");
    const dim   = new THREE.Color("#0a1628");

    for (let i = 0; i < count; i++) {
      pos[i * 3]     = (Math.random() - 0.5) * 40;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 24;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 20;

      const r = Math.random();
      const c = r > 0.97 ? green : r > 0.92 ? blue : dim;
      col[i * 3]     = c.r;
      col[i * 3 + 1] = c.g;
      col[i * 3 + 2] = c.b;
    }
    return [pos, col];
  }, [count]);

  useFrame(({ clock, mouse }) => {
    if (!mesh.current) return;
    mesh.current.rotation.y = clock.getElapsedTime() * 0.012;
    mesh.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.008) * 0.08;
    if (light.current) {
      light.current.position.x = mouse.x * 8;
      light.current.position.y = mouse.y * 5;
    }
  });

  return (
    <>
      <pointLight ref={light} position={[0, 0, 5]} intensity={0.6} color="#00ff88" />
      <points ref={mesh}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[positions, 3]} />
          <bufferAttribute attach="attributes-color"    args={[colors, 3]}    />
        </bufferGeometry>
        <pointsMaterial
          size={0.06}
          vertexColors
          transparent
          opacity={0.8}
          sizeAttenuation
        />
      </points>
    </>
  );
}

function GlobeWireframe() {
  const mesh = useRef();
  useFrame(({ clock }) => {
    if (!mesh.current) return;
    mesh.current.rotation.y = clock.getElapsedTime() * 0.08;
    mesh.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.04) * 0.1;
  });
  return (
    <mesh ref={mesh} position={[4, 0, -8]}>
      <sphereGeometry args={[4, 24, 24]} />
      <meshBasicMaterial color="#00ff88" wireframe transparent opacity={0.04} />
    </mesh>
  );
}

function ScanRing() {
  const ring = useRef();
  useFrame(({ clock }) => {
    if (!ring.current) return;
    ring.current.rotation.z = clock.getElapsedTime() * 0.3;
    ring.current.rotation.x = Math.PI / 2 + Math.sin(clock.getElapsedTime() * 0.2) * 0.3;
  });
  return (
    <mesh ref={ring} position={[0, 0, -6]}>
      <torusGeometry args={[6, 0.015, 6, 120]} />
      <meshBasicMaterial color="#00d4ff" transparent opacity={0.15} />
    </mesh>
  );
}

export default function ParticleField({ className = "" }) {
  return (
    <Canvas
      className={className}
      camera={{ position: [0, 0, 12], fov: 60 }}
      gl={{ antialias: true, alpha: true }}
      style={{ background: "transparent" }}
    >
      <ambientLight intensity={0.1} />
      <Particles />
      <GlobeWireframe />
      <ScanRing />
    </Canvas>
  );
}
