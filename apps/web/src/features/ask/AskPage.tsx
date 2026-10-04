import { PageHeader } from '../../components/ui/PageHeader'
import { SampleBadge } from '../../components/ui/SampleBadge'
import { StateCard } from '../../components/ui/StateCard'

export function AskPage() {
  return (
    <div className="flex flex-col gap-3 px-5 pt-5">
      <PageHeader title="Ask" trailing={<SampleBadge />} />
      <StateCard title="Coming soon">
        Ask questions about your team and get answers with cited evidence (WEB-009).
      </StateCard>
    </div>
  )
}
