import * as THREE from 'three'
import { useRef, useState, useEffect } from 'react'
import { Canvas, extend, useThree, useFrame } from '@react-three/fiber'
import { useGLTF, useTexture, Environment, Lightformer, OrbitControls } from '@react-three/drei'

useGLTF.preload('/model.glb')
//useTexture.preload('')

export default function ModelView() {
  return (
    <Canvas camera={{ position: [0, 0, 10], fov: 25 }}>
      <ambientLight intensity={Math.PI} />
      <Model />
    </Canvas>
  )
}

function Model() {
  const gltf = useGLTF('/model.glb')
  const modelRef = useRef<THREE.Mesh>(null)
  return (
    <>
      <OrbitControls 
        enableZoom={true}
        enablePan={true}
        enableRotate={true}
        minDistance={5}
        maxDistance={500}
        autoRotate={true}
        rotation={[0, 0, 0]}
        rotateSpeed={0.5}
      />
      <primitive 
        ref={modelRef}
        object={gltf.scene}
        scale={0.18}
        position={[0, 0, 0]}
      />
    </>
  )
}