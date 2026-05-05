// schunk_hand.js — Schunk SVH Hand kinematic builder for Three.js
// Joint data from schunk_svh_hand_right_glb.urdf (Schunk GmbH)
// All units in metres; meshes exported in metres.

import * as THREE from '/chiros/static/js/three/three.module.js';

const MESH_BASE = '/chiros/static/models/schunk_hand/';

// ── Kinematic chain ───────────────────────────────────────────────────────────
// [jointName, parentLink, childLink, xyz, rpy, axis]
const JOINT_DEFS = [
  // Fixed base chain
  ['root_joint', 'base_link',            'right_hand_base_link', [0,0,0],                   [0,0,-1.5708],      [0,0,1]],
  ['f4',         'right_hand_base_link', 'right_hand_e1',         [0,-0.01313,0],            [0,0,0],            [0,0,1]],
  // Thumb
  ['Thumb_Opposition', 'right_hand_e1', 'right_hand_z',          [-0.0169,0.02626,0],        [0,0.2618,1.5708],  [0,0,-1]],
  ['Thumb_Flexion',    'right_hand_z',  'right_hand_a',           [0,0,0.04596],             [1.5708,-0.6004,1.5708],[0,0,1]],
  ['j3',               'right_hand_a',  'right_hand_b',           [0.0485,0,0],              [0,0,0],            [0,0,1]],
  ['j4',               'right_hand_b',  'right_hand_c',           [0.0300,0,0],              [0,0,0],            [0,0,1]],
  // Index finger (spread_fixed is fixed offset from e1)
  ['index_spread_fixed',         'right_hand_e1',        'right_hand_virtual_l', [-0.025,0,0.110],    [0,-1.5707,1.5707], [0,0,1]],
  ['Index_Finger_Proximal',      'right_hand_virtual_l', 'right_hand_l',          [0,0,0],            [-1.5707,0,0],      [0,0,1]],
  ['Index_Finger_Distal',        'right_hand_l',         'right_hand_p',          [0.04804,0,0],      [0,0,0],            [0,0,1]],
  ['j14',                        'right_hand_p',         'right_hand_t',          [0.026,0,0],        [0,0,0],            [0,0,1]],
  // Middle finger (middle_spread_dummy is fixed)
  ['middle_spread_dummy',        'right_hand_e1',        'right_hand_virtual_k', [0,0,0.110],         [0,-1.5707,1.5707], [0,0,1]],
  ['Middle_Finger_Proximal',     'right_hand_virtual_k', 'right_hand_k',          [0,0,0],            [-1.5707,0,0],      [0,0,1]],
  ['Middle_Finger_Distal',       'right_hand_k',         'right_hand_o',          [0.05004,0,0],      [0,0,0],            [0,0,1]],
  ['j15',                        'right_hand_o',         'right_hand_s',          [0.032,0,0],        [0,0,0],            [0,0,1]],
  // Ring & Pinky (via e2 intermediate link, j5 mimic of Opposition kept at rest)
  ['j5_fixed',           'right_hand_e1',        'right_hand_e2',         [0.0184,0.006,0.0375],  [0,0,0],          [0,0,1]],
  ['ring_spread_fixed',  'right_hand_e2',        'right_hand_virtual_j',  [0.003855,-0.006,0.0655],[-1.5707,-1.5707,0],[0,0,1]],
  ['Ring_Finger',        'right_hand_virtual_j', 'right_hand_j',          [0,0,0],                [1.5707,0,0],     [0,0,1]],
  ['j16',                'right_hand_j',         'right_hand_r',          [0.04454,0,0],          [0,0,0],          [0,0,1]],
  ['pinky_spread_fixed', 'right_hand_e2',        'right_hand_virtual_i',  [0.025355,-0.006,0.056],[-1.5707,-1.5707,0],[0,0,1]],
  ['Pinky',              'right_hand_virtual_i', 'right_hand_i',          [0,0,0],                [1.5707,0,0],     [0,0,1]],
  ['j13',                'right_hand_i',         'right_hand_m',          [0.04454,0,0],          [0,0,0],          [0,0,1]],
  ['j17',                'right_hand_m',         'right_hand_q',          [0.022,0,0],            [0,0,0],          [0,0,1]],
];

// ── Link visuals ──────────────────────────────────────────────────────────────
// Visual xyz taken from URDF <visual><origin> — several Schunk links have non-zero offsets.
const LINK_VISUALS = [
  ['right_hand_base_link', 'base10.glb',     [0, 0,       -0.032],   [0,0,0]],
  ['right_hand_e1',        'h10.glb',        [0, 0.01313,  0],       [0,0,0]],
  ['right_hand_e2',        'h11.glb',        [-0.0007, 0, -0.01002], [0,0,0]],
  // Thumb
  ['right_hand_z',         'd10.glb',        [0, 0,  0.02442],       [0,0,0]],
  ['right_hand_a',         'd11.glb',        [0,0,0],                [0,0,0]],
  ['right_hand_b',         'd12.glb',        [0,0,0],                [0,0,0]],
  ['right_hand_c',         'd13.glb',        [0,0,0],                [0,0,0]],
  // Index
  ['right_hand_virtual_l', 'f10_f20.glb',    [0, 0,  0.01321],       [0,0,0]],
  ['right_hand_l',         'f11.glb',        [0,0,0],                [0,0,0]],
  ['right_hand_p',         'f12.glb',        [0,0,0],                [0,0,0]],
  ['right_hand_t',         'finger_tip.glb', [0,0,0],                [0,0,0]],
  // Middle
  ['right_hand_virtual_k', 'f10_f20.glb',    [0, 0,  0.01321],       [0,0,0]],
  ['right_hand_k',         'f21.glb',        [0,0,0],                [0,0,0]],
  ['right_hand_o',         'f22_f32.glb',    [0,0,0],                [0,0,0]],
  ['right_hand_s',         'finger_tip.glb', [0,0,0],                [0,0,0]],
  // Ring
  ['right_hand_virtual_j', 'f30_f40.glb',    [0, 0, -0.01321],       [0,0,0]],
  ['right_hand_j',         'f31.glb',        [0,0,0],                [0,0,0]],
  ['right_hand_r',         'finger_tip.glb', [0,0,0],                [0,0,0]],
  // Pinky
  ['right_hand_virtual_i', 'f30_f40.glb',    [0, 0, -0.01321],       [0,0,0]],
  ['right_hand_i',         'f41.glb',        [0,0,0],                [0,0,0]],
  ['right_hand_m',         'f42.glb',        [0,0,0],                [0,0,0]],
  ['right_hand_q',         'finger_tip.glb', [0,0,0],                [0,0,0]],
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

export async function buildSchunkHand(loader, isRight) {
  const links  = {};
  const joints = {};

  const forearm = new THREE.Group();
  forearm.name = 'base_link';
  links['base_link'] = forearm;

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
            color: 0x2a3040, roughness: 0.55, metalness: 0.45,
            clearcoat: 0.2, clearcoatRoughness: 0.35,
          });
        }
      });
      link.add(mesh);
    } catch (e) {
      console.warn('[SchunkHand] mesh not loaded:', file, e.message);
    }
  }));

  // URDF: Z = finger direction after root_joint fixed rotation — same convention as Shadow
  forearm.rotation.set(Math.PI / 2, Math.PI, 0);

  const handRoot = new THREE.Group();
  handRoot.add(forearm);

  if (isRight) {
    handRoot.scale.set(1.1, 1.1, 1.1);
    handRoot.position.set(0.28, -0.10, 0);
  } else {
    handRoot.scale.set(-1.1, 1.1, 1.1);
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
