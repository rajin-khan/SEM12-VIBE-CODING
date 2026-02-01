# Introduction to Software Development
## Overview of Software Components
In software development, there are three primary components: Databases (DBs), Clients, and Servers. The client is typically an application or a website that interacts with the server, which in turn interacts with the database. To mitigate vulnerability issues, it's a common practice to restrict direct client access to the database.

## Separation of Codebase
The codebase is usually separated into two distinct parts: Client code and Server code. This separation is crucial for maintaining a secure and scalable architecture. The server exposes Application Programming Interfaces (API Endpoints) that allow clients to access its functionality without directly interacting with the database.

## API Endpoints and Libraries
API Endpoints are interfaces that enable clients to interact with servers. In the past, even local API Endpoints were referred to as APIs. However, with the evolution of software development, the term API now typically refers to remote interfaces that provide access to functionality developed by others. When interacting with local code, we often refer to it as a library. Computers prefer to communicate with servers using HTTP requests and receive structured responses, such as JSON (JavaScript Object Notation) or XML (Extensible Markup Language), which are more efficient for machine interpretation.

## Authentication and Authorization
Authentication and Authorization are two fundamental concepts in software security:
* **Authentication** refers to the process of verifying the identity of a user or system. It's a mechanism to ensure that the user or system is who they claim to be.
* **Authorization** refers to the process of determining what actions an authenticated user or system can perform. It's a mechanism to control access to resources and functionality.

### Examples
* Authentication: A user logs in to a website with their username and password.
* Authorization: After logging in, the user is granted access to certain features or resources based on their role or permissions.

## Software Development Life Cycle (SDLC)
The SDLC, also known as the Vibe Coding SDLC, consists of the following stages:
1. **The Plan**: Define the project's objectives, scope, and requirements.
2. **Design**: Create software and user interface designs.
3. **Code Generation**: Write the code for the project.
4. **Test (Verify)**: Perform automated testing to ensure the code meets the requirements.
5. **Ship it!**: Deploy the software to production.
6. **Maintain**: Continuously maintain and update the software to ensure it remains relevant and secure.

## Change Management and Code Quality
When modifying code, it's essential to consider the dependencies and potential impact on the entire system. Splitting or copying logic across multiple functions can lead to maintenance issues and should be avoided. Instead, strive for a singular, well-organized codebase that is easy to modify and maintain.

## Pitfalls of Casual Code Generation
Using AI-generated code can introduce several pitfalls:
* **Hallucinations**: AI may create functions that don't exist or are not relevant to the project.
* **Security Blindness**: AI-generated code may be insecure, potentially leading to data leaks or other security issues.
* **Performance**: AI-generated code can be "heavy" and may not perform well under heavy loads.

## Best Practices
To avoid these pitfalls, follow these guidelines:
* If you didn't write the code, you are still responsible for it. Read and review the code before using it.
* Use AI tools and agents as tools, not as the leading force behind your project.
* Prioritize proper systems and architecture over quick fixes or one-shotted solutions.

## Expectations from the Course
This course aims to cover the following topics:
* **Frontend**: Client-side development, including user interface and user experience.
* **Backend**: Server-side development, including API design and database interaction.
* **Authentication vs Authorization**: Understanding the differences between authentication and authorization, and how to implement them securely.
* **Proper Systems**: Designing and developing scalable, maintainable, and secure software systems.