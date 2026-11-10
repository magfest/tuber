import './requestGroups.css'

// Which roommates in a room are tied together by roommate requests.
// Only groups of two or more get a background; someone on their own gets none.
export interface RequestGroupTag {
  index: number
  className: string
  title: string
}

export function requestGroupTags (groups: number[][] | undefined, names: { [badge: string]: string }): { [badge: string]: RequestGroupTag } {
  const tags: { [badge: string]: RequestGroupTag } = {}
  let index = 0
  for (const members of groups || []) {
    if (members.length < 2) {
      continue
    }
    const title = 'Roommate request group: ' + members.map((badge) => names[badge] || badge).join(', ')
    for (const badge of members) {
      tags[badge] = { index, className: 'request-group-bg request-group-bg-' + (index % 4), title }
    }
    index++
  }
  return tags
}
