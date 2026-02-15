import { Poke } from "poke";

const poke = new Poke({ apiKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4OTUyMzJlYS0zM2RmLTRkNTItODdiYy03Yjk3MDExMmM2NTAiLCJqdGkiOiJmZmI4NDIwNS1kNGY1LTQ1NmYtODcwNS03MWE2NzM5NzlmZTMiLCJpYXQiOjE3NzExMjA4NDAsImV4cCI6MjA4NjQ4MDg0MH0.XLPsDa8hmR7cfJbuErl60ScSEMmlj7RYwq9_ZCWCrsc" });

// Send a message to your agent
await poke.sendMessage("book something in calendar");
console.log("Done");
