// ability_hand.js — Ability Hand kinematic builder for Three.js
// Joint data from ability_hand_right_glb.urdf (PSYONIC)
// All units in metres; meshes exported in metres.

import * as THREE from '/chiros/static/js/three/three.module.js';

const MESH_BASE = '/chiros/static/models/ability_hand/';

// ── Kinematic chain ───────────────────────────────────────────────────────────
// [jointName, parentLink, childLink, xyz, rpy, axis]
const JOINT_DEFS = [
  // Fixed joints establishing palm geometry
  ['base_joint',  'base_link', 'base',       [0,0,0],                                          [0,0,-1.5708],                    [0,0,1]],
  ['wrist2thumb', 'base',      'thumb_base', [-0.0240476665,0.00378124745,0.0323296492],         [3.14148426,-0.08848813,-3.14036612],[0,0,1]],
  // Thumb (both joints are independently driven)
  ['thumb_q1',    'thumb_base','thumb_L1',   [0,0,0],                                          [3.14159,-0.08848,-3.14159],       [0,0,1]],
  ['thumb_q2',    'thumb_L1',  'thumb_L2',   [0.0278283501,1.74e-19,0.0147507],                [1.832595714,-0,5.37e-18],         [0,0,1]],
  // Index
  ['index_q1',    'thumb_base','index_L1',   [0.00949,-0.01304,-0.06295],                      [-1.1595426,1.284473,-1.0510017],  [0,0,1]],
  ['index_q2',    'index_L1',  'index_L2',   [0.038472723,0.003257695,0],                      [0,0,0.084474],                   [0,0,1]],
  // Middle
  ['middle_q1',   'thumb_base','middle_L1',  [-0.009653191,-0.015310271,-0.067853949],          [-1.2810617,1.308458,-1.2453757],  [0,0,1]],
  ['middle_q2',   'middle_L1', 'middle_L2',  [0.038472723,0.003257695,0],                      [0,0,0.084474],                   [0,0,1]],
  // Ring
  ['ring_q1',     'thumb_base','ring_L1',    [-0.02995426,-0.014212492,-0.067286105],           [-1.4249947,1.321452,-1.4657307],  [0,0,1]],
  ['ring_q2',     'ring_L1',   'ring_L2',    [0.038472723,0.003257695,0],                      [0,0,0.084474],                   [0,0,1]],
  // Pinky
  ['pinky_q1',    'thumb_base','pinky_L1',   [-0.049521293,-0.011004583,-0.063029065],          [-1.3764827,1.32222,-1.4832097],   [0,0,1]],
  ['pinky_q2',    'pinky_L1',  'pinky_L2',   [0.038472723,0.003257695,0],                      [0,0,0.084474],                   [0,0,1]],
];

// ── Link visuals ──────────────────────────────────────────────────────────────
// Visual xyz/rpy taken directly from URDF <visual><origin> elements.
const LINK_VISUALS = [
  // base (wristmesh.glb excluded — large file); base_link has no visual
  ['thumb_base', 'FB_palm_ref_MIR.glb', [0, 0, 0],                               [0, 0, 0]],
  ['thumb_L1',   'thumb-F1-MIR.glb',   [0.0278284, 0, 0.0147507],                [1.832596, 0, 0]],
  ['thumb_L2',   'thumb-F2.glb',       [0.065187,  0.023340, 0.003935],           [-3.14159, 0, 0.34383]],
  // Index/middle/ring/pinky L1: mesh sits at the distal end of the proximal segment
  ['index_L1',   'idx-F1.glb',         [0.038473, 0.003258, 0],                   [0, 0, 0.084474]],
  ['index_L2',   'idx-F2.glb',         [0.0091241, 0, 0],                         [0, 0, 0]],
  ['middle_L1',  'idx-F1.glb',         [0.038473, 0.003258, 0],                   [0, 0, 0.084474]],
  ['middle_L2',  'idx-F2.glb',         [0.0091241, 0, 0],                         [0, 0, 0]],
  ['ring_L1',    'idx-F1.glb',         [0.038473, 0.003258, 0],                   [0, 0, 0.084474]],
  ['ring_L2',    'idx-F2.glb',         [0.0091241, 0, 0],                         [0, 0, 0]],
  ['pinky_L1',   'idx-F1.glb',         [0.038473, 0.003258, 0],                   [0, 0, 0.084474]],
  ['pinky_L2',   'idx-F2.glb',         [0.0091241, 0, 0],                         [0, 0, 0]],
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

export async function buildAbilityHand(loader, isRight) {
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
            color: 0x303848, roughness: 0.6, metalness: 0.3,
            clearcoat: 0.15, clearcoatRoughness: 0.4,
          });
        }
      });
      link.add(mesh);
    } catch (e) {
      console.warn('[AbilityHand] mesh not loaded:', file, e.message);
    }
  }));

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
