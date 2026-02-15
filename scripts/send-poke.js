#!/usr/bin/env node
/**
 * Send a message to a Poke via the official SDK.
 * Usage: node send-poke.js <api_key> <message>
 * Exits 0 on success, 1 on failure. Writes error to stderr.
 */
import { Poke } from "poke";

const [apiKey, message] = process.argv.slice(2);
if (!apiKey || !message) {
  process.stderr.write("Usage: node send-poke.js <api_key> <message>\n");
  process.exit(1);
}

try {
  const poke = new Poke({ apiKey });
  await poke.sendMessage(message);
  process.exit(0);
} catch (err) {
  process.stderr.write(String(err.message || err) + "\n");
  process.exit(1);
}
