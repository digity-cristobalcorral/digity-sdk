// allegro_hand.js — Allegro Hand N16 kinematic builder for Three.js
// Joint data from allegro_hand_right_glb.urdf (Wonik Robotics)
// All units in metres; meshes are exported in metres (no scale conversion needed).

import * as THREE from '/chiros/static/js/three/three.module.js';

const MESH_BASE = '/chiros/static/models/allegro_hand/';

// ── Kinematic chain ───────────────────────────────────────────────────────────
// [jointName, parentLink, childLink, xyz, rpy, axis]
const JOINT_DEFS = [
  // Index finger (joints 0–3)
  ['joint_0.0', 'base_link', 'link_0.0', [0, 0.0435, -0.001542], [-0.08727,0,0],  [0,0,1]],
  ['joint_1.0', 'link_0.0',  'link_1.0', [0, 0,      0.0164   ], [0,0,0],         [0,1,0]],
  ['joint_2.0', 'link_1.0',  'link_2.0', [0, 0,      0.054    ], [0,0,0],         [0,1,0]],
  ['joint_3.0', 'link_2.0',  'link_3.0', [0, 0,      0.0384   ], [0,0,0],         [0,1,0]],
  // Middle finger (joints 4–7) — share finger meshes with index
  ['joint_4.0', 'base_link', 'link_4.0', [0, 0,      0.0007   ], [0,0,0],         [0,0,1]],
  ['joint_5.0', 'link_4.0',  'link_5.0', [0, 0,      0.0164   ], [0,0,0],         [0,1,0]],
  ['joint_6.0', 'link_5.0',  'link_6.0', [0, 0,      0.054    ], [0,0,0],         [0,1,0]],
  ['joint_7.0', 'link_6.0',  'link_7.0', [0, 0,      0.0384   ], [0,0,0],         [0,1,0]],
  // Ring finger (joints 8–11)
  ['joint_8.0',  'base_link', 'link_8.0',  [0, -0.0435, -0.001542], [0.08727,0,0], [0,0,1]],
  ['joint_9.0',  'link_8.0',  'link_9.0',  [0,  0,       0.0164  ], [0,0,0],       [0,1,0]],
  ['joint_10.0', 'link_9.0',  'link_10.0', [0,  0,       0.054   ], [0,0,0],       [0,1,0]],
  ['joint_11.0', 'link_10.0', 'link_11.0', [0,  0,       0.0384  ], [0,0,0],       [0,1,0]],
  // Thumb (joints 12–15)
  ['joint_12.0', 'base_link',  'link_12.0', [-0.0182, 0.019333, -0.045987], [0,-1.65806,-1.5708], [-1,0,0]],
  ['joint_13.0', 'link_12.0',  'link_13.0', [-0.027, 0.005, 0.0399],        [0,0,0],               [0,0,1]],
  ['joint_14.0', 'link_13.0',  'link_14.0', [0, 0, 0.0177],                 [0,0,0],               [0,1,0]],
  ['joint_15.0', 'link_14.0',  'link_15.0', [0, 0, 0.0514],                 [0,0,0],               [0,1,0]],
];

// ── Link visuals ──────────────────────────────────────────────────────────────
// [linkName, meshFile, visualXYZ, visualRPY]
const LINK_VISUALS = [
  ['base_link',  'base_link.glb',       [0,0,0], [0,0,0]],
  // Index
  ['link_0.0',   'link_0.0.glb',        [0,0,0], [0,0,0]],
  ['link_1.0',   'link_1.0.glb',        [0,0,0], [0,0,0]],
  ['link_2.0',   'link_2.0.glb',        [0,0,0], [0,0,0]],
  ['link_3.0',   'link_3.0.glb',        [0,0,0], [0,0,0]],
  // Middle (share index meshes)
  ['link_4.0',   'link_0.0.glb',        [0,0,0], [0,0,0]],
  ['link_5.0',   'link_1.0.glb',        [0,0,0], [0,0,0]],
  ['link_6.0',   'link_2.0.glb',        [0,0,0], [0,0,0]],
  ['link_7.0',   'link_3.0.glb',        [0,0,0], [0,0,0]],
  // Ring (share index meshes)
  ['link_8.0',   'link_0.0.glb',        [0,0,0], [0,0,0]],
  ['link_9.0',   'link_1.0.glb',        [0,0,0], [0,0,0]],
  ['link_10.0',  'link_2.0.glb',        [0,0,0], [0,0,0]],
  ['link_11.0',  'link_3.0.glb',        [0,0,0], [0,0,0]],
  // Thumb
  ['link_12.0',  'link_12.0_right.glb', [0,0,0], [0,0,0]],
  ['link_13.0',  'link_13.0.glb',       [0,0,0], [0,0,0]],
  ['link_14.0',  'link_14.0.glb',       [0,0,0], [0,0,0]],
  ['link_15.0',  'link_15.0.glb',       [0,0,0], [0,0,0]],
];

// ── GLB cache ─────────────────────────────────────────────────────────────────
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

// ── Public builder ────────────────────────────────────────────────────────────
export async function buildAllegroHand(loader, isRight) {
  const links  = {};
  const joints = {};

  const root = new THREE.Group();
  root.name = 'base_link';
  links['base_link'] = root;

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
      // Allegro meshes are in metres — no unit conversion needed
      mesh.position.set(vxyz[0], vxyz[1], vxyz[2]);
      mesh.quaternion.copy(rpyQuat(vrpy[0], vrpy[1], vrpy[2]));
      mesh.traverse(o => {
        if (o.isMesh) {
          o.castShadow    = true;
          o.receiveShadow = true;
          o.material = new THREE.MeshPhysicalMaterial({
            color: 0x8898b0, roughness: 0.5, metalness: 0.5,
            clearcoat: 0.25, clearcoatRoughness: 0.3,
          });
        }
      });
      link.add(mesh);
    } catch (e) {
      console.warn('[AllegroHand] mesh not loaded:', file, e.message);
    }
  }));

  // Orient so fingers point up in scene (URDF: Z = finger direction)
  root.rotation.set(Math.PI / 2, Math.PI, 0);

  const handRoot = new THREE.Group();
  handRoot.add(root);

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
