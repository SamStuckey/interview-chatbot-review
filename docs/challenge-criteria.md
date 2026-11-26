# AI-Powered Chat Agent for Carton Caps 

Carton Caps is an app that empowers consumers to raise money for the schools
they care about while buying the everyday products they love. In this
hypothetical example, the app is already full-featured and publicly available.
The Carton Caps team is now exploring how AI can enhance user engagement and
support smarter decision-making across the platform.

You've been brought in to prototype an AI-driven conversational assistant for
the Carton Caps app. The Carton Caps team wants to create an engaging, helpful
in-app chat agent that can assist users in finding personalized product
recommendations and understanding the referral process.

To do this, your task is to design and build a proof-of-concept AI service that
leverages LLM technology and user context to maintain natural, helpful
conversations through an API endpoint.

You can assume the app uses an existing REST API that accounts for the
following (you don’t need to design these):

- User authentication
- New user registration

## Considerations for solution design:

- How will the chatbot ensure that its responses remain aligned with its purpose?
- How will the system handle updates to data and knowledge base changes? (This
  can be documented in the system definition or illustration and does not need to
  be implemented as a part of the challenge.)
- A mock dataset and supporting context information are provided in the attached zip file for convenience.

We recognize that your time is valuable and limited. Although we do expect your
prototype to work, rather than completing every detail of this open-ended
challenge, we encourage you to focus your effort on the aspects of the solution
that most interest or excite you. For areas you choose not to implement in
code, feel free to include brief documentation or notes outlining your
approach. This helps us understand your thinking, even if you didn’t have time
to fully build it out.

*Please note that submitting code produced by generative AI is prohibited.*

## Deliverable #1: Conversational AI Design + LLM Strategy Create a technical specification for an AI-powered chat agent API. 
Your spec should include:

- A clear definition of the API contract, creating and maintaining conversations with users.
- Relevant diagrams that illustrate the system to onboard future engineers to your solution.
- How the API could be integrated into the Carton Caps mobile app.

Where appropriate, provide documentation on privacy considerations,
conversation design principles, trade-offs, and reasoning behind LLM-generated
outputs.

*We're especially interested in seeing your point of view: why you made the
design/LLM decisions you did, what you prioritized, and how you might evolve
the approach over time.*

 
## Deliverable #2: Prototype Conversational AI Service Implement a prototyped AI service that fulfills the above API contract. 
This should include:

- A working API that creates and maintains multi-turn conversations.
- A minimal LLM integration or simulation that powers the conversations. It should demonstrate how a real system would work.
- Any preprocessing, prompt engineering, or context management needed to generate relevant responses.
- Unit and/or integration tests for your service and conversation logic.

Hint: We're a senior team that values craft and clarity. We'll be looking for:
- Thoughtfulness in your LLM approach and conversation design trade-offs
- Sensible, clean, and testable code structure
- A clear perspective on real-world conversational AI considerations (e.g., context management, memory limitations, dialogue coherence)
- Your ability to handle diverse user intents and maintain conversation flow
- Realism in how this prototype could evolve into a production-ready solution
