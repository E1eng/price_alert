# Robinhood Chain MCAP → Telegram Alert

Monitors a Robinhood Chain token and sends Telegram when market cap crosses upward through your targets.

Default token:
`0x63ee90921eac3c3f87961c17556bb3ebdf2490a9`

Setup:
1. Create a Telegram bot with `@BotFather` using `/newbot`.
2. Send `/start` to the bot and obtain your chat ID.
3. Create a GitHub repository and upload these files.
4. GitHub → Settings → Secrets and variables → Actions.
5. Add repository secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
6. Add repository variables: `TOKEN_ADDRESS`, `MCAP_THRESHOLDS`.
7. Example: `MCAP_THRESHOLDS=5000000,10000000,20000000`.
8. Actions → Run workflow.

The workflow checks every ~30 seconds while running and is scheduled about every 5 minutes. GitHub scheduled jobs can be delayed, so this is not tick-by-tick trading infrastructure.

No wallet or private key is required.
