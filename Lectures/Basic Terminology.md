You have DBs, Clients, and Server code in between them.

We usually don't let the client access the DB due to vulnerability issues.

The codebase will be separated between Client code and Server code.

Servers expose an Application Programming Interface (API Endpoints) to allow the Client to access them.

In the past, these API Endpoints (even if running locally, meaning all the code is available on my own computer), would be an API, but if only local, these days we just call them a library.

API these days refer to the fact that a certain person somewhere has written some code, we don't want to code up that functionality locally, so we access it via an API. Humans access it via a GUI, which is inefficient, but computers prefer other things, more efficient.

The computer sends requests, and receives structured responses over HTTP. Browsers have been doing this forever, so we just prefer this method of communication. Responses should differ, ideally, from what is suitable for humans, if it is to be interpreted by computers efficiently (this may be as JSON [full form], XML [full form], or any other kind of structured data) because it is easier to extract info that way).

Diffs between Authentication and Authorization (with examples). Authentication is easy with Vibe Coding, Authorization is kinda hard. 

Vibe coding SDLC (Soft Dev Life Cycle):

1. The plan (the VIBE DUDE)
2. Design (Software Design and UI Design)
3. Code Gen
4. Test (Verify) [Automated Testing]
5. Ship it!
6. Maintain (Loop back to step 1, The plan)

Software is never finished, always maintained.

When changing code, take note of all the dependencies. If you fuck up a single module with a singular responsibility, it fucks up all the dependencies too.

Splitting/Copying the same logic across different functions is bad. We have to first identify where everything is, then modify every instance. We want a singular place to edit.

These problems are all a part of change management.

Pitfalls of Casual Code Generation:

Hallucinations: AI creates functions that doesn't exist.
Security Blindness: AI Generates code that works but is insecure (leaks data) [but getting better rapidly], it's just good to have an idea of the security risks of your work.
Performance: AI code is often "heavy" - it works for one user, but crashes for 1000. Maybe by default, but we can make it better with improvements.

A simple rule of thumb: If you didn't write it, you are still responsible for it. Read before you run.

The first project will be fully local.
Expectations from the course: 
Frontend, Backend
Authentication vs Authorization (AuthN vs AuthZ)
Proper systems aren't one-shotted.
Use AI Tools and Agents as Tools, not Leading your project.