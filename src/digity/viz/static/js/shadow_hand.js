// shadow_hand.js — Shadow Hand E3M5 kinematic builder for Three.js
// Joint data from shadow_hand_right_glb.urdf (Shadow Robot Company, BSD License)
// All units in meters (GLB meshes are in mm, scaled 0.001).

import * as THREE from '/chiros/static/js/three/three.module.js';

const MESH_BASE = '/chiros/static/models/shadow_hand/';

// ── Kinematic chain ───────────────────────────────────────────────────────────
// [jointName, parentLink, childLink, xyz, rpy, revolute-axis]
const JOINT_DEFS = [
  // Wrist
  ['WRJ2', 'forearm',      'wrist',        [ 0,      -0.010,  0.213  ], [0,0,0],            [0,1,0]],
  ['WRJ1', 'wrist',        'palm',         [ 0,       0,       0.034 ], [0,0,0],            [1,0,0]],
  // First (index) finger
  ['FFJ4', 'palm',         'ffknuckle',    [ 0.033,   0,       0.095 ], [0,0,0],            [0,-1,0]],
  ['FFJ3', 'ffknuckle',    'ffproximal',   [ 0,       0,       0     ], [0,0,0],            [1,0,0]],
  ['FFJ2', 'ffproximal',   'ffmiddle',     [ 0,       0,       0.045 ], [0,0,0],            [1,0,0]],
  ['FFJ1', 'ffmiddle',     'ffdistal',     [ 0,       0,       0.025 ], [0,0,0],            [1,0,0]],
  // Middle finger
  ['MFJ4', 'palm',         'mfknuckle',    [ 0.011,   0,       0.099 ], [0,0,0],            [0,-1,0]],
  ['MFJ3', 'mfknuckle',    'mfproximal',   [ 0,       0,       0     ], [0,0,0],            [1,0,0]],
  ['MFJ2', 'mfproximal',   'mfmiddle',     [ 0,       0,       0.045 ], [0,0,0],            [1,0,0]],
  ['MFJ1', 'mfmiddle',     'mfdistal',     [ 0,       0,       0.025 ], [0,0,0],            [1,0,0]],
  // Ring finger
  ['RFJ4', 'palm',         'rfknuckle',    [-0.011,   0,       0.095 ], [0,0,0],            [0,1,0]],
  ['RFJ3', 'rfknuckle',    'rfproximal',   [ 0,       0,       0     ], [0,0,0],            [1,0,0]],
  ['RFJ2', 'rfproximal',   'rfmiddle',     [ 0,       0,       0.045 ], [0,0,0],            [1,0,0]],
  ['RFJ1', 'rfmiddle',     'rfdistal',     [ 0,       0,       0.025 ], [0,0,0],            [1,0,0]],
  // Little finger
  ['LFJ5', 'palm',         'lfmetacarpal', [-0.033,   0,       0.021 ], [0,-0.9599,0],      [1,0,0]],
  ['LFJ4', 'lfmetacarpal', 'lfknuckle',   [ 0.054,   0,       0.038 ], [0, 0.9599,0],      [0,1,0]],
  ['LFJ3', 'lfknuckle',    'lfproximal',   [ 0,       0,       0     ], [0,0,0],            [1,0,0]],
  ['LFJ2', 'lfproximal',   'lfmiddle',     [ 0,       0,       0.045 ], [0,0,0],            [1,0,0]],
  ['LFJ1', 'lfmiddle',     'lfdistal',     [ 0,       0,       0.025 ], [0,0,0],            [1,0,0]],
  // Thumb
  ['THJ5', 'palm',         'thbase',       [ 0.034,  -0.00858, 0.029 ], [-0.7854,0,-1.5708],[0,0,-1]],
  ['THJ4', 'thbase',       'thproximal',   [ 0,       0,       0     ], [0,0,0],            [0,1,0]],
  ['THJ3', 'thproximal',   'thhub',        [ 0,       0,       0.038 ], [0,0,0],            [0,1,0]],
  ['THJ2', 'thhub',        'thmiddle',     [ 0,       0,       0     ], [0,0,0],            [1,0,0]],
  ['THJ1', 'thmiddle',     'thdistal',     [ 0,       0,       0.032 ], [0,0,0],            [1,0,0]],
];

// ── Link visuals ──────────────────────────────────────────────────────────────
// [linkName, meshFile, visualXYZ, visualRPY]
const LINK_VISUALS = [
  ['forearm',      'forearm_E3M5.glb',       [0,0,0],       [0,0,0]     ],
  ['wrist',        'wrist_E3M5.glb',         [0,0,0],       [0,0,0]     ],
  ['palm',         'palm_E3M5.glb',          [0,0,0],       [0,0,0]     ],
  ['ffknuckle',    'f_knuckle_E3M5.glb',     [0,0,0.0005],  [0,0,0]     ],
  ['ffproximal',   'f_proximal_E3M5.glb',    [0,0,0],       [0,0,0]     ],
  ['ffmiddle',     'f_middle_E3M5.glb',      [0,0,0],       [0,0,0]     ],
  ['ffdistal',     'f_distal_pst.glb',       [0,0,0],       [0,0,0]     ],
  ['mfknuckle',    'f_knuckle_E3M5.glb',     [0,0,0.0005],  [0,0,0]     ],
  ['mfproximal',   'f_proximal_E3M5.glb',    [0,0,0],       [0,0,0]     ],
  ['mfmiddle',     'f_middle_E3M5.glb',      [0,0,0],       [0,0,0]     ],
  ['mfdistal',     'f_distal_pst.glb',       [0,0,0],       [0,0,0]     ],
  ['rfknuckle',    'f_knuckle_E3M5.glb',     [0,0,0.0005],  [0,0,0]     ],
  ['rfproximal',   'f_proximal_E3M5.glb',    [0,0,0],       [0,0,0]     ],
  ['rfmiddle',     'f_middle_E3M5.glb',      [0,0,0],       [0,0,0]     ],
  ['rfdistal',     'f_distal_pst.glb',       [0,0,0],       [0,0,0]     ],
  ['lfmetacarpal', 'lf_metacarpal_E3M5.glb', [0,0,0],       [0,0.9599,0]],
  ['lfknuckle',    'f_knuckle_E3M5.glb',     [0,0,0.0005],  [0,0,0]     ],
  ['lfproximal',   'f_proximal_E3M5.glb',    [0,0,0],       [0,0,0]     ],
  ['lfmiddle',     'f_middle_E3M5.glb',      [0,0,0],       [0,0,0]     ],
  ['lfdistal',     'f_distal_pst.glb',       [0,0,0],       [0,0,0]     ],
  ['thproximal',   'th_proximal_E3M5.glb',   [0,0,0],       [0,0,1.5708]],
  ['thmiddle',     'th_middle_E3M5.glb',     [0,0,0],       [0,0,1.5708]],
  ['thdistal',     'th_distal_pst.glb',      [0,0,0],       [0,0,0]     ],
];

// ── GLB cache (shared across instances) ───────────────────────────────────────
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
export async function buildShadowHand(loader, isRight) {
  const links  = {};
  const joints = {};

  // Root link
  const forearm = new THREE.Group();
  forearm.name = 'forearm';
  links['forearm'] = forearm;

  // Build joint/link hierarchy
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

  // Load meshes and attach to link nodes
  await Promise.all(LINK_VISUALS.map(async ([linkName, file, vxyz, vrpy]) => {
    const link = links[linkName];
    if (!link) return;
    try {
      const scene = await fetchGlb(loader, file);
      const mesh  = scene.clone(true);
      mesh.scale.setScalar(0.001);  // mm → m
      mesh.position.set(vxyz[0], vxyz[1], vxyz[2]);
      mesh.quaternion.copy(rpyQuat(vrpy[0], vrpy[1], vrpy[2]));
      mesh.traverse(o => {
        if (o.isMesh) {
          o.castShadow    = true;
          o.receiveShadow = true;
          o.material = new THREE.MeshPhysicalMaterial({
            color: 0x888ea0, roughness: 0.55, metalness: 0.45,
            clearcoat: 0.2, clearcoatRoughness: 0.3,
          });
        }
      });
      link.add(mesh);
    } catch (e) {
      console.warn('[ShadowHand] mesh not loaded:', file, e.message);
    }
  }));

  // ── Wrapper: orient + position in scene ───────────────────────────────────
  // Shadow URDF: Z = finger direction (up), X = thumb side.
  // Rotate forearm so fingers point upward in scene (same as Ultraleap).
  // URDF: Z=fingers(up), X=thumb side, Y=palm normal.
  // Rotate so fingers point up in scene and palm faces camera.
  forearm.rotation.set(Math.PI / 2, Math.PI, 0);

  const handRoot = new THREE.Group();
  handRoot.add(forearm);

  // Scale to match scene size: Shadow hand ~0.20 m palm-to-tip → ~0.24 scene units
  if (isRight) {
    handRoot.scale.set(1.2, 1.2, 1.2);
    handRoot.position.set(0.28, -0.10, 0);
  } else {
    handRoot.scale.set(-1.2, 1.2, 1.2);   // mirror left hand on X
    handRoot.position.set(-0.28, -0.10, 0);
  }

  // ── API ───────────────────────────────────────────────────────────────────
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
