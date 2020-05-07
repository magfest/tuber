import Vue from 'vue';

function checkPermission(operation, event, department) {
  const { perms } = this.$store.state.user;
  for (let i = 0; i < perms.length; i += 1) {
    const perm = perms[i];
    if (event && (perm.event !== null) && (event !== perm.event)) {
      continue;
    }
    if (department && (perm.department !== null) && (department !== perm.department)) {
      continue;
    }
    const permEntity = perm.operation.split('.')[0];
    const permOp = perm.operation.split('.')[1];
    const reqEntity = operation.split('.')[0];
    const reqOp = operation.split('.')[1];
    if (permEntity !== '*' && (permEntity !== reqEntity)) {
      continue;
    }
    if (permOp !== '*' && (permOp !== reqOp)) {
      continue;
    }
    return true;
  }
  return false;
}

Vue.mixin({ methods: { checkPermission } });

export default { checkPermission };
