import { Text } from './fields'
import type { Books } from './stream'

/** The custodian's ledger beside the coins at the custody address, compared after each step. */
export function BooksPanel({ books, before }: { books: Books | null; before: Books | null }) {
  if (!books) {
    return (
      <section className="card books">
        <h2>Books and chain</h2>
        <p className="muted">
          The custodian's ledger and the coins at the custody address appear here once the
          custody key exists, and are compared after every step.
        </p>
      </section>
    )
  }
  return (
    <section className="card books">
      <h2>Books and chain</h2>
      <p className={`reconcile ${books.reconciled ? 'ok' : 'bad'}`}>
        Ledger {books.owed} {books.reconciled ? '=' : '≠'} coins {books.held}
      </p>
      <h3>Ledger: what the custodian owes</h3>
      <table className="ledger">
        <tbody>
          {Object.entries(books.ledger).map(([client, balance]) => (
            <tr key={client} className={before?.ledger[client] !== balance ? 'changed' : ''}>
              <td>{client}</td>
              <td>{balance}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Chain: coins at the custody address</h3>
      {books.coins.length === 0 ? (
        <p className="muted">none yet</p>
      ) : (
        <ul className="coins">
          {books.coins.map((c) => {
            const [txid, vout] = c.coin.split(':')
            const seen = before?.coins.some((b) => b.coin === c.coin)
            return (
              <li key={c.coin} className={seen ? '' : 'new'}>
                <strong>{c.amount}</strong>
                <span className="muted">{c.origin}</span>
                <span className="muted">
                  output {vout} of <Text text={txid} />
                </span>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
