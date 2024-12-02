import * as THREE from 'three'
import { useRef, useState, useEffect, Suspense } from 'react'
import { Canvas, extend, useThree, useFrame } from '@react-three/fiber'
import { useGLTF, useTexture, Environment, Lightformer, OrbitControls } from '@react-three/drei'

useGLTF.preload('/model.glb')
//useTexture.preload('')

export default function ModelView() {
  return (
    <Suspense fallback={<Fallback/>}>
      <Canvas camera={{ position: [0, 0, 10], fov: 25 }} fallback={<h1>OpenGL isnt supported</h1>}>
        <ambientLight intensity={Math.PI} />
        <Model />
      </Canvas>
    </Suspense>
  )
}


function Fallback() {
  return (
    <>
      <div className="w-full h-full flex items-center justify-center">
        <h1 className='text-xl' >Loading 3D model...</h1>
      </div>
    </>
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
        maxDistance={50}
        //autoRotate={true}
        //rotation={[0, 0, 0]}
        //rotateSpeed={0.5}
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