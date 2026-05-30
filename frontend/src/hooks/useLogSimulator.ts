import { useEffect, useRef } from 'react'

const LOG_TYPES = ['INIT', 'LINK', 'RESOLVE', 'GEO', 'MATCH', 'INFO']
const LOG_MESSAGES = [
  'Syncing nodal state to main database',
  'Cross-referencing entity #92 with external registries',
  'Detected potential spoofing attempt in packet stream',
  'Resolving high-velocity transaction chains',
  'New leaf node attached to cluster alpha',
  'Updating temporal weights for reconstruction',
  'Ingesting metadata from evidence shard #42',
]

export function useLogSimulator(containerId: string, intervalMs = 3000) {
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const logFeed = document.getElementById(containerId)
    if (!logFeed) return

    function addLog() {
      if (!logFeed) return
      const time = new Date().toLocaleTimeString([], { hour12: false })
      const type = LOG_TYPES[Math.floor(Math.random() * LOG_TYPES.length)]
      const msg = LOG_MESSAGES[Math.floor(Math.random() * LOG_MESSAGES.length)]

      const div = document.createElement('div')
      div.className = 'flex gap-2'
      div.innerHTML = `<span style="color:#bec7d4">[${time}]</span> <span style="color:${type === 'INIT' || type === 'INFO' ? '#98cbff' : '#feb700'};font-weight:500">${type}</span> <span>${msg}</span>`

      logFeed.appendChild(div)
      logFeed.scrollTop = logFeed.scrollHeight

      if (logFeed.children.length > 50) {
        logFeed.removeChild(logFeed.children[0])
      }
    }

    intervalRef.current = setInterval(addLog, intervalMs)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [containerId, intervalMs])
}
