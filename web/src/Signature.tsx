import { useEffect, useState } from 'react'
import { Hex } from './fields'
import { toBtc, toSats } from './reserves'
import { checkSnapshot, type SnapshotCheck, type SnapshotDocument } from './snapshot'

const ONE_BTC = 100_000_000n

function lowered(snapshot: SnapshotDocument): SnapshotDocument {
  return { ...snapshot, liabilities: toBtc(toSats(String(snapshot.liabilities)) - ONE_BTC) }
}

/** The client's check that the custodian signed the snapshot its balance check relies on. */
export function SignatureCheck({ snapshot }: { snapshot: SnapshotDocument }) {
  const [altered, setAltered] = useState(false)
  const [check, setCheck] = useState<SnapshotCheck | null>(null)
  const shown = altered ? lowered(snapshot) : snapshot

  useEffect(() => {
    let current = true
    checkSnapshot(altered ? lowered(snapshot) : snapshot).then(
      (result) => current && setCheck(result),
    )
    return () => {
      current = false
    }
  }, [snapshot, altered])

  const signed = check?.messageMatches && check.signatureValid
  return (
    <div className="card signature">
      <h2>Check the custodian's signature</h2>
      <p>
        The root above is worth checking only if the custodian is bound to it. The snapshot names
        the root, the totals, the block it was taken at and the latest audit-log fingerprint, and
        two of the three signers signed it with the custody key. This page rebuilds the signed
        message from the snapshot's own fields and checks the signature.
      </p>
      <p className="muted">
        The signature is checked with <code>@noble/curves</code>, an audited secp256k1 library
        (<code>web/src/snapshot.ts</code>), which shares no code with the server's verifier.
      </p>
      <dl className="fields">
        <dt>liabilities</dt>
        <dd>
          {String(shown.liabilities)} BTC{altered && ' (lowered by 1 BTC on this page)'}
        </dd>
        <dt>assets</dt>
        <dd>{String(shown.assets)} BTC</dd>
        <dt>liabilities root</dt>
        <dd>
          <Hex text={String(shown.liabilities_root)} />
        </dd>
        <dt>custody key</dt>
        <dd>
          <Hex text={shown.custody_output_key} />
        </dd>
        <dt>message, recomputed</dt>
        <dd>{check && <Hex text={check.message} />}</dd>
        <dt>message, published</dt>
        <dd>
          <Hex text={shown.attestation.message} />
        </dd>
        <dt>signature</dt>
        <dd>
          <Hex text={shown.attestation.bip340_signature} />
        </dd>
      </dl>
      <div className="claim">
        <button type="button" className="secondary" onClick={() => setAltered((a) => !a)}>
          {altered ? 'Restore the published figures' : 'Lower the liabilities by 1 BTC'}
        </button>
      </div>
      {check && (
        <p className={`verdict ${signed ? 'ok' : 'bad'}`}>
          {signed
            ? 'Signed. The custody key signed exactly these figures: the recomputed message equals the published one, and the signature verifies over it.'
            : `Not signed. The recomputed message ${check.messageMatches ? 'equals' : 'differs from'} the published one, and the signature ${check.signatureValid ? 'verifies' : 'does not verify'} over it: the custody key did not sign these figures.`}
        </p>
      )}
    </div>
  )
}
