## **Part 1: AI Assisted Coding** - Answers

1. **Current Workflow:** How do you currently use AI tools (e.g., ChatGPT, Cursor, Claude, MCPs, Agents) to assist or generate code? Do you use them differently for AI-specific tasks (e.g., designing a RAG pipeline) versus general backend work?

I heavily use AI tools for code generation, and it's safe to say that lately (last 6 months) the vast majority of the code I produce is written by AI Agents. At work I use Claude Code, but I try to keep a simple setup and build my workflow around open standards (i.e. mcp/skills) rather than provider-specific features (like Claude Code subagents, loops, etc). For my personal use, I prefer pi.dev as it's more minimalistic and tweakable, with OpenRouter as a LLM provider (lately the default LLM has been DeepSeek V4 Flash for its great cost/performance balance).

I wouldn't say that I use coding agents in a specifically different way for backend vs AI-specific tasks, but rather that I have a common workflow that allows me to tailor the approach to task at hand. What I usually do is use the official maintained Agent Skills of the framework I'm using, to make sure my agents use the correct APIs and have an updated context on how to use the library in scope. This translates to searching for and using various skills for different kinds of work: for backend stuff it would be FastAPI and SQLModel skills for example, for AI agents, LangChain has a set of well maintained skills, in this project I used official skills from Qdrant.

On top of this, one thing I've started doing consistently as the amount of work I delegated to an agent increased, is to rely heavily on spec-driven-development. Taking inspiration from the major public SDD frameworks [Spec-Kit](https://github.com/github/spec-kit) and [OpenSpec](https://github.com/Fission-AI/openspec), I developed a custom skill for enforcing the methodology (you can see it in .claude/skills/sdd). The great upside is that by using this workflow, the specs compound in the sdd/ folder and over time build a living documentation that can be used as context for following tasks, increasing the consistency and the level of control. This has been central in my approach to AI assisted coding and I've had great results so far.

As opposed to skills, of which I am a heavy user and endorser, I don't use MCP much (for personal coding). The only server I've been using with some consistency lately is [Codegraph](https://github.com/colbymchenry/codegraph). It's a local MCP server that parses the codebase in a graph db and exposes a single tool for exploration, which is more efficient on big codebases than the long sequence of tools the agent would call without it. I've had a good experience so far but I wouldn't say this is a necessary component for me.

---

2. **The Good & The Bad:** Where do you see the biggest value in AI-assisted development? What are the current limitations or risks, especially when building systems that will themselves be consumed by AI agents?

The biggest value for me lies in speed of execution, depth of the developed solution and upskilling possibilities. I think that by using coding assistants in the right way, a developer can build much more complex and deep solutions to the tasks at hand, in a faster way. While doing so, by working at the edge/limit of one's knowledge, I believe that upskilling is very much possible to obtain in this way, by putting in the effort: by continuously questioning AI and asking for deep explanation on topics one's not a master of, a dev can slowly build additional skills and widen his capabilities.

With that said, the downside is that you don't have to use it as I described (so doublechecking the output, asking for explanations on what is not clear and using all the best practices): one can simply "blindly" trust AI. This obviously brings many problems like loss of codebase control, important decisions delegated, and the classic accumulation of "AI slop".

Another downside, that comes with what I described as proper usage and can lead to improper usage, is cognitive overload: as we moved from executors to supervisors, the amount of actually complex brain work (considering tradeoffs, making technical decisions, considering the bigger picture) has increased and that can lead to tiredness/burnout, with the consequence of leaning more towards improper/brainless usage of AI tools. For me here the solution is to simply slow down: if AI can make us 10x faster and brain-drained OR 5x faster without going crazy, I would choose the latter 100% of the time.

---

3. **The Future:** How do you envision your role as an AI Product Engineer evolving over the next few years? What skills do you think will matter most as LLMs get better at writing code?

It's safe to assume that the trend of AI agents actually producing most of the code will continue, and the capabilities of those systems will only get better.

With this in mind, I believe one hard and one soft skill will become increasingly more important for any engineer and especially for an AI Engineer. The hard skill I think will be very important is system architecture: as AI Agents are better and better at implementation, we have to become better and more aware in designing and planning the bigger picture. The only way we can use AI properly is to have the skills to check what it does, and even if not down to the specifics of a library/language, we have to keep a grip on the bigger picture, know the tradeoffs, have the basic knowledge to know when to push back without relying on it blindly.

On the other side, as Agents do and humans coordinate, it will be ever more important to have sharp communication skills. Not because we need to talk better to agents (it's not rocket science), but because, if the majority of work is executed by agents and the bottleneck becomes not execution speed but human brain speed, what will be important for us is going to be planning and coordinating with other colleagues efficiently, in order to be able to use agents effectively without getting lost.
