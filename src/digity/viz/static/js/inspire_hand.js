// inspire_hand.js — Inspire Hand kinematic builder for Three.js
// Joint data from inspire_hand_right.urdf
// All units in metres; meshes exported in metres.

import * as THREE from '/chiros/static/js/three/three.module.js';

const MESH_BASE = '/chiros/static/models/inspire_hand/';

// ── Kinematic chain ───────────────────────────────────────────────────────────
// [jointName, parentLink, childLink, xyz, rpy, axis]
const JOINT_DEFS = [
  // Fixed base joint: rotates hand_base_link from world frame
  ['base_joint',               'base',              'hand_base_link',      [0,0,0],                    [-1.5708,0,3.14159],  [0,0,1]],
  // Thumb
  ['thumb_proximal_yaw_joint', 'hand_base_link',    'thumb_proximal_base', [-0.01696,-0.0691,-0.02045], [1.5708,-1.5708,0],  [0,0,-1]],
  ['thumb_proximal_pitch_joint','thumb_proximal_base','thumb_proximal',    [-0.0088099,0.010892,-0.00925],[1.5708,0,2.8587],  [0,0,1]],
  ['thumb_intermediate_joint', 'thumb_proximal',    'thumb_intermediate',  [0.04407,0.034553,-0.0008],  [0,0,0],             [0,0,1]],
  ['thumb_distal_joint',       'thumb_intermediate','thumb_distal',        [0.020248,0.010156,-0.0012], [0,0,0],             [0,0,1]],
  // Index
  ['index_proximal_joint',     'hand_base_link',    'index_proximal',      [0.00028533,-0.13653,-0.032268],[-3.1067,0,0],    [0,0,1]],
  ['index_intermediate_joint', 'index_proximal',    'index_intermediate',  [-0.0026138,0.032026,-0.001],[0,0,0],             [0,0,1]],
  // Middle
  ['middle_proximal_joint',    'hand_base_link',    'middle_proximal',     [0.00028533,-0.1371,-0.01295],[-3.1416,0,0],     [0,0,1]],
  ['middle_intermediate_joint','middle_proximal',   'middle_intermediate', [-0.0024229,0.032041,-0.001],[0,0,0],             [0,0,1]],
  // Ring
  ['ring_proximal_joint',      'hand_base_link',    'ring_proximal',       [0.00028533,-0.13691,0.0062872],[3.0892,0,0],    [0,0,1]],
  ['ring_intermediate_joint',  'ring_proximal',     'ring_intermediate',   [-0.0024229,0.032041,-0.001],[0,0,0],             [0,0,1]],
  // Pinky
  ['pinky_proximal_joint',     'hand_base_link',    'pinky_proximal',      [0.00028533,-0.13571,0.025488],[3.0369,0,0],     [0,0,1]],
  ['pinky_intermediate_joint', 'pinky_proximal',    'pinky_intermediate',  [-0.0024229,0.032041,-0.001],[0,0,0],             [0,0,1]],
];

// ── Link visuals ──────────────────────────────────────────────────────────────
const LINK_VISUALS = [
  ['hand_base_link',    'right_base_link.glb',          [0,0,0], [0,0,0]],
  // Thumb
  ['thumb_proximal_base','right_thumb_proximal_base.glb',[0,0,0],[0,0,0]],
  ['thumb_proximal',    'right_thumb_proximal.glb',      [0,0,0], [0,0,0]],
  ['thumb_intermediate','right_thumb_intermediate.glb',  [0,0,0], [0,0,0]],
  ['thumb_distal',      'right_thumb_distal.glb',        [0,0,0], [0,0,0]],
  // Index
  ['index_proximal',    'right_index_proximal.glb',      [0,0,0], [0,0,0]],
  ['index_intermediate','right_index_intermediate.glb',  [0,0,0], [0,0,0]],
  // Middle (share index proximal mesh)
  ['middle_proximal',   'right_index_proximal.glb',      [0,0,0], [0,0,0]],
  ['middle_intermediate','right_middle_intermediate.glb',[0,0,0], [0,0,0]],
  // Ring (share index meshes)
  ['ring_proximal',     'right_index_proximal.glb',      [0,0,0], [0,0,0]],
  ['ring_intermediate', 'right_index_intermediate.glb',  [0,0,0], [0,0,0]],
  // Pinky
  ['pinky_proximal',    'right_index_proximal.glb',      [0,0,0], [0,0,0]],
  ['pinky_intermediate','right_pinky_intermediate.glb',  [0,0,0], [0,0,0]],
];

const _cache = {};
function fetchGlb(loader, file) {
  if (!_cache[file]) {
    _cache[file] = new Promise((resolve, reject) =>
      loader.load(MESH_BASE + file, g => resolve(g.scene), undefined, reject)
    );
  }
  return _cache[file];
}

function rpyQuat(r, p, y) {
  return new THREE.Quaternion().setFromEuler(new THREE.Euler(r, p, y, 'ZYX'));
}

export async function buildInspireHand(loader, isRight) {
  const links  = {};
  const joints = {};

  const forearm = new THREE.Group();
  forearm.name = 'base';
  links['base'] = forearm;

  for (const [jName, parentLinkName, childLinkName, xyz, rpy, axisArr] of JOINT_DEFS) {
    const jNode = new THREE.Group();
    jNode.name  = 'j_' + jName;
    jNode.position.set(xyz[0], xyz[1], xyz[2]);
    const restQ = rpyQuat(rpy[0], rpy[1], rpy[2]);
    jNode.quaternion.copy(restQ);

    const cNode = new THREE.Group();
    cNode.name = childLinkName;

    jNode.add(cNode);
    if (links[parentLinkName]) links[parentLinkName].add(jNode);

    links[childLinkName] = cNode;
    joints[jName] = { node: jNode, restQ, axis: new THREE.Vector3(...axisArr) };
  }

  await Promise.all(LINK_VISUALS.map(async ([linkName, file, vxyz, vrpy]) => {
    const link = links[linkName];
    if (!link) return;
    try {
      const scene = await fetchGlb(loader, file);
      const mesh  = scene.clone(true);
      mesh.position.set(vxyz[0], vxyz[1], vxyz[2]);
      mesh.quaternion.copy(rpyQuat(vrpy[0], vrpy[1], vrpy[2]));
      mesh.traverse(o => {
        if (o.isMesh) {
          o.castShadow    = true;
          o.receiveShadow = true;
          o.material = new THREE.MeshPhysicalMaterial({
            color: 0xa0a8b8, roughness: 0.45, metalness: 0.4,
            clearcoat: 0.3, clearcoatRoughness: 0.25,
          });
        }
      });
      link.add(mesh);
    } catch (e) {
      console.warn('[InspireHand] mesh not loaded:', file, e.message);
    }
  }));

  // Orient so fingers point up; base_joint fixed offset handles URDF→scene alignment
  forearm.rotation.set(Math.PI / 2, Math.PI, 0);

  const handRoot = new THREE.Group();
  handRoot.add(forearm);

  if (isRight) {
    handRoot.scale.set(1.2, 1.2, 1.2);
    handRoot.position.set(0.28, -0.10, 0);
  } else {
    handRoot.scale.set(-1.2, 1.2, 1.2);
    handRoot.position.set(-0.28, -0.10, 0);
  }

  const _rotQ = new THREE.Quaternion();

  function setJoint(name, radians) {
    const j = joints[name];
    if (!j) return;
    _rotQ.setFromAxisAngle(j.axis, radians);
    j.node.quaternion.copy(j.restQ).multiply(_rotQ);
  }

  function dispose() {
    handRoot.traverse(o => {
      if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); }
    });
    handRoot.parent?.remove(handRoot);
  }

  return { root: handRoot, setJoint, dispose };
}
