import { useStore } from '../store'

const store = useStore()
function checkPermission (permission: string) {
  let permissions: string[] = []
  if (Object.prototype.hasOwnProperty.call(store.getters.permissions, '*')) {
    permissions = store.getters.permissions['*']
  }
  if (store.getters.event) {
    if (Object.prototype.hasOwnProperty.call(store.getters.permissions, String(store.getters.event.id))) {
      permissions = permissions.concat(store.getters.permissions[String(store.getters.event.id)])
    }
  }
  return evalPermission(permission, permissions)
}

function checkDepartmentPermission (permission: string, department: number) {
  if (store.getters.event) {
    return evalPermission(permission, store.getters.departmentPermissions[String(store.getters.event.id)][department])
  }
  return evalPermission(permission, [])
}

function evalPermission (permission: string, permissions: string[]): boolean {
  const parts = permission.split('.')
  const entity = parts[0]
  const instance = parts[1]
  const operation = parts[2]
  let result: boolean = false
  permissions.forEach((perm) => {
    const permParts = perm.split('.')
    const permEntity = permParts[0]
    const permInstance = permParts[1]
    const permOperation = permParts[2]
    if (permEntity !== '*' && permEntity !== entity) {
      return
    }
    if (permInstance !== '*' && permInstance !== instance) {
      return
    }
    if (permOperation !== '*' && permOperation !== operation) {
      return
    }
    result = true
  })
  return result
}

export {
  checkPermission,
  checkDepartmentPermission
}
