// The key inside a Taproot address, decoded in the browser.
//
// A Taproot address is the witness version (1) and the 32-byte output key, written in bech32m
// (BIP 350) with the network's prefix: bc on the public network, bcrt on regtest. Decoding it gives
// back the key that controls the coins at that address, without asking the custodian. Decoding
// uses @scure/base. tests/demo/test_browser_address.py checks it against addresses Bitcoin Core
// derives from known keys.

import { bech32m } from '@scure/base'
import { hex } from './reserves.ts'

export interface TaprootAddress {
  prefix: string // "bc" or "bcrt"
  key: string // the 32-byte x-only output key, hex
}

/** The output key inside a Taproot address; throws on any other kind of address. */
export function taprootKey(address: string): TaprootAddress {
  const { prefix, words } = bech32m.decode(address as `${string}1${string}`)
  const program = bech32m.fromWords(words.slice(1))
  if (words[0] !== 1 || program.length !== 32) {
    throw new Error(`${address} is not a Taproot address (witness version ${words[0]})`)
  }
  return { prefix, key: hex(program) }
}
