"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

// ═══════════ ANIMATED SPHERE ═══════════
function GlowSphere({ position, color, speed, distort, scale }: {
  position: [number, number, number];
  color: string;
  speed: number;
  distort: number;
  scale: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null!);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = state.clock.elapsedTime * speed * 0.3;
      meshRef.current.rotation.y = state.clock.elapsedTime * speed * 0.2;
    }
  });

  return (
    <Float speed={speed * 2} rotationIntensity={0.4} floatIntensity={0.8}>
      <mesh ref={meshRef} position={position} scale={scale}>
        <icosahedronGeometry args={[1, 4]} />
        <MeshDistortMaterial
          color={color}
          roughness={0.2}
          metalness={0.8}
          distort={distort}
          speed={speed}
          transparent
          opacity={0.7}
        />
      </mesh>
    </Float>
  );
}

// ═══════════ PARTICLE FIELD ═══════════
function ParticleField() {
  const count = 200;
  const pointsRef = useRef<THREE.Points>(null!);

  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 15;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 15;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 15;
    }
    return arr;
  }, []);

  useFrame((state) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y = state.clock.elapsedTime * 0.03;
      pointsRef.current.rotation.x = state.clock.elapsedTime * 0.02;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color="#FF6B35"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}

// ═══════════ ORBITAL RINGS ═══════════
function OrbitalRing({ radius, speed, color, tilt }: {
  radius: number;
  speed: number;
  color: string;
  tilt: number;
}) {
  const ringRef = useRef<THREE.Mesh>(null!);

  useFrame((state) => {
    if (ringRef.current) {
      ringRef.current.rotation.z = state.clock.elapsedTime * speed;
    }
  });

  return (
    <mesh ref={ringRef} rotation={[tilt, 0, 0]}>
      <torusGeometry args={[radius, 0.008, 16, 100]} />
      <meshBasicMaterial color={color} transparent opacity={0.25} />
    </mesh>
  );
}

// ═══════════ 3D SCENE ═══════════
function Scene() {
  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[5, 5, 5]} intensity={1} color="#FF6B35" />
      <pointLight position={[-5, -3, 3]} intensity={0.5} color="#3B82F6" />
      <pointLight position={[0, 5, -5]} intensity={0.4} color="#8B5CF6" />

      {/* Main glowing sphere — represents GENESIS AI core */}
      <GlowSphere position={[0, 0, 0]} color="#FF6B35" speed={1} distort={0.4} scale={1.2} />

      {/* 6 smaller spheres — represent 6 agents */}
      <GlowSphere position={[2.5, 1, -1]} color="#3B82F6" speed={1.5} distort={0.3} scale={0.35} />
      <GlowSphere position={[-2.2, 0.8, 0.5]} color="#10B981" speed={1.2} distort={0.35} scale={0.3} />
      <GlowSphere position={[1.5, -1.5, 1]} color="#8B5CF6" speed={1.8} distort={0.25} scale={0.28} />
      <GlowSphere position={[-1.8, -1.2, -0.8]} color="#F59E0B" speed={1.3} distort={0.3} scale={0.32} />
      <GlowSphere position={[0.5, 2, 0.8]} color="#06B6D4" speed={1.6} distort={0.28} scale={0.25} />
      <GlowSphere position={[-0.8, -2.2, 1.2]} color="#EC4899" speed={1.4} distort={0.32} scale={0.27} />

      {/* Orbital rings */}
      <OrbitalRing radius={3} speed={0.15} color="#FF6B35" tilt={0.5} />
      <OrbitalRing radius={3.8} speed={-0.1} color="#3B82F6" tilt={1.2} />
      <OrbitalRing radius={4.5} speed={0.08} color="#8B5CF6" tilt={0.8} />

      {/* Particle field */}
      <ParticleField />
    </>
  );
}

// ═══════════ EXPORTED COMPONENT ═══════════
export default function Hero3D() {
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 0,
        pointerEvents: "none",
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 6], fov: 55 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <Scene />
      </Canvas>
    </div>
  );
}
