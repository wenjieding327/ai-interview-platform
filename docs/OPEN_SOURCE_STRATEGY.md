# Open Source and Anti-Copy Strategy

## Current Recommendation

Keep the repository public enough for recruiters and judges to inspect, but do not expose the most valuable future assets:

- Premium question banks
- High-quality evaluation datasets
- Production prompts
- User data
- Organization dashboard logic
- Commercial analytics

## Three License Paths

### Path A: No License Yet

Best when the project is mainly a portfolio and you are still deciding commercialization.

Effect:

- People can view the public repository.
- They do not automatically receive broad reuse rights.
- Recruiters can still inspect your work.

Tradeoff:

- It is not friendly to outside contributors.
- It is less likely to become a classic open-source community project.

### Path B: AGPL-3.0

Best when you want real open-source credibility while reducing the risk of closed-source SaaS clones.

Effect:

- Others can use and modify the code.
- If they run a modified network service, they generally need to provide source code for the modified version.

Tradeoff:

- Commercial use is still possible.
- Some companies avoid AGPL projects.

### Path C: Source-Available Noncommercial

Best when you want people to read the code but do not want commercial reuse.

Effect:

- You can prohibit commercial use.
- Good for a portfolio or demo project.

Tradeoff:

- This is not traditional open source.
- It may reduce community adoption.

## Practical Anti-Copy Measures

- Keep API keys and production secrets only in Vercel/Railway variables.
- Keep premium data and prompts out of the public repo.
- Add clear screenshots, commit history, demo video, and docs that prove authorship.
- Use GitHub releases or tags before public launch.
- Put your name/contact in README and docs.
- Keep a private roadmap for commercial features.

## Suggested Next Step

For the current stage, keep the code public for job applications and add a clear license only after choosing the goal:

- Job search first: no license or source-available noncommercial.
- Open-source reputation first: AGPL-3.0.
- Commercial product first: keep core code private and publish a limited demo repo.
