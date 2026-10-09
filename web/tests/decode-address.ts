// Reads a JSON list of addresses on stdin and prints, for each, the key web/src/address.ts decodes
// from it, or the error. Driven by tests/demo/test_browser_address.py.
import { readFileSync } from 'node:fs'
import { taprootKey } from '../src/address.ts'

const addresses = JSON.parse(readFileSync(0, 'utf8')) as string[]
console.log(
  JSON.stringify(
    addresses.map((a) => {
      try {
        return taprootKey(a)
      } catch (error) {
        return { error: String(error) }
      }
    }),
  ),
)
