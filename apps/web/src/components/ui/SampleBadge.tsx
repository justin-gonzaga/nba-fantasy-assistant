import { useIsSample } from '../../api/client'
import { Badge } from './Badge'

export function SampleBadge() {
  if (!useIsSample()) return null
  return <Badge tone="accent">Sample data</Badge>
}
