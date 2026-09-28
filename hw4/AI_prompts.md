# AI Prompts: HW4 (Campus Customs)

## Problem 1: Vibe Coder Prompts

**Prompt:**

> we are going to build a customer facing website with a helpful chatbot. It's going to be for "Campus Customs", which is a business that sales Yale University merchandise. The information I've given you so far includes a database and images of products that should align with the database. We are going to do this in steps according to the assignment, so don't get ahead of me. Reacy?

**Follow-up:**

> ok new project called HW3 - see the folder in our main directory? there is some source information there

## Problem 2: Analyze the database

**Prompt:**

> Problem 2: Analyze the database. For this problem please look at the campus_customs.db file and figure out what is in it (there are tables with fields). Create a file output/harness.md and in that file you will write each table and its fields and a short line on why each field matters for the shop and/or the chatbot. We will be adding more to this file later

## Problem 3: Build the Campus Customs website

**Prompt:**

> Problem 3: Build the Campus Customs website. Look at yalebulldogblue.com to pull campus customs consistent wording (but don't copy text for Home or About Us) then scaffold a react+vite+typescipt fron end for Campus Customs. Put a nav bar at the top that links to the main pages including Home, Products, About Us, Log in, Create Account.  For products, show the product images from the catalog (use the database paths) and add basic product information like name, price, and a short description. Clicking a product should open a single-item page (put product image on left, full product text on the right (description, price, sizes/stock). Don't worry if you don't have all the informaiont yet. Put a chat interface in the bottom right of the site (ok to be floating) - don't worry about opening communication with an agent yet, just leave a stub for now. Start a simple FastAPI app in backend/main.py to serve products and images that we will grow into the agent in a later problem

## Problem 4: Create account and login

**Prompt:**

> Problem 4: Create account and login.  Okay so we are going to make the create account and log-in functions work and add new accounts into the users table and store passwords securely from human or AI hackers.  Use the test@campuscustoms.yale.edu with password=password to test. Update our harness file with how authorization works (i.e., what you store for a user and how passwords are protected)

## Problem 5: PydanticAI agent backend

**Prompt:**

> Problem 5: PydanticAI agent backend. Okay time to build the chatbot as a pydanticAI agent behind FastAPI. Put the API app in backend/main.py to be run with uvicorn. Create backend/prompts/ptompt.md for system prompts, backend/agent.py for agent entry/wiring, backend/tools.py for tools the agent can call and backend/models.py for pydantic and pydanticAI structured types. In main.py make sure a message from the website returns a reply from the agent (and whatever else needed for products and authorization). Put campus customs voice and safety basics into prompt.md and start or update types in models.py for chat replies and product cards as needed. In harness.md note how the front end interacts with fastAPI and how the agent is loaded (prompt file and model). make sure the backend runs from the backend folder like this: uvicorn main:app --reload --port 8000. By the way you have may portkey key right?

## Problem 6: Tools: product info and stock

**Prompt:**

> Problem 6: Tools: product info and stock. Add a tool to allow looking up real information from the database file including product description, price, and how many are in stock (by size when asked). The agent can only use the database and not invent anything. It should clearly report when something is out of stock. Make sure prompt.md is updated so the agent knows to call the tool for price and stock questions. Add or update return types in models.py., and in harness list each tool and explain which model fields you chose for looking up results and why

**Follow-up:**

> the chatbot used the word 'surfaced' in a jargon-y way. Is there a way to get the chatbot to not use jargon?

## Problem 7: Chat search that updates the page

**Prompt:**

> Problem 7: Chat search that updates the page. Okay so I noticed in our chatbot you already have a function to show some of the product cards, which is great, but I believe we are being asked to have the main webpage update with the product cards the chatbot is identifying. This will allow more room and a more natural interface for the user to look through the items. It's okay to keep the chatbot results in the chatbot too for the 'top' items, but while you are at it please add soft arrows to show the user that they can scroll horizontally within the chatbot results. The product cards in the main webpage should bring the user to the single-item page just like if they had been browsing. Update prompts/prompt.md and harnessmd so it is clear how search results reach the page

## Problem 8: Customer memory

**Prompt:**

> Problem 8: Customer memory. Ok so now we do the chat history for customers who are logged in by putting it in an appropriate table in the data base and pulling it up when the cutsomer logs in again. The agent should know their name and e-mail. This feels a bit unrelated but we also want there to be enough page context visible to the agent so a customer can ask a question about a product they are looking at without specifying the product. Document in harness how the user chat history is stored, what customer fields the agent sees, and how page context is passed

## Problem 9: Usability improvements

**Prompt:**

> Problem 9: Usability improvements. We are supposed to at 2 front-end usability improvements and 2 backend/agent usability improvements. Whatever we decide to do should be documented in output/usability.md including what was added and why/how it helps either the shopper, business, or both. Can you give me a few ideas for each?

**Follow-up:**

> let's go with your recommendation (F1, F2, B1, B2)

## Problem 10: Style the website

**Prompt:**

> Problem 10: Style the website. Ok so now we are supposed to add some creative design to the site to make it feel like a real Campus Customs storefront. Fonts, color, hierarchy, motion, product presentation, and chat feel should among the things considered. When we've decided on a sufficiently creative version, write a concise output/design.md with what we changed and why it should help customers stick around and buy. Make a first pass at this

**Follow-up:**

> The Y in the circle and the font for "Yale" do not match the Yale look/font but should. We are a licensed retailer and can use that. I don't like "We're just off campus" - it's okay to say we are in the commercial heart of Yale at 57 Broadway

**Follow-up:**

> the only thing is that the Y by itself in the circle should match the athletic Y which is symmetric across a vertical line in the center. Can you see what the Y's look like in YALE on the clothes items? That's what the Y should look like in this context

**Follow-up:**

> it's not a good match. Look at the YALE in the top left of this website

**Follow-up:**

> yes do that, but also reverse color on the Y and center it better in the white ring it will be in

**Follow-up:**

> the Yale above bulldogblue looks like it's right justified rather than centered. It will look better centered

**Follow-up:**

> ok just make the white circle around the Y thinner - maybe half the thickness

**Follow-up:**

> ok let's go with this

## Problem 11: Site testing (app check)

**Prompt:**

> Problem 11: Site testing (app check). Okay so you've already been testing our site repeatedly but now we are being asked to test the site and document the testing in output/app_check.html, which should be a double-clickable html.  I think you have checked all of these already (and I have double-checked you), but here's the list: chat checking the inventory level/price of an item from the database, that the dynamic search-results cards appear after a category questions, one of the usability features added in Problem 9. The app_check html should be easy for the teaching assistants to grade so make a heading for each check, include a screenshot, include one or two sentences on what the screenshot proves. Put the screenshot image files in output/app_check_images/ and link them from app_check.html with relative paths (like app_check_images/inventory.png)

## Problem 12: Audit trail, safety, finish harness

**Prompt:**

> Problem 12: Audit trail, safety, finish harness. For this problem keep an append-only output/audit_trail.json of all agent-loop activity like time, tool name, short arguments/results and stop reason. Do not wipe it between runs. Also think of some safety rules to give the agent and put them in prompts/prompt.md. Fiinish harness/md so it is clear how the system works. Include model fields in models.py and why you chose them, tools and abilities, safety rules, and specs like loop limits, result caps, models, how to run front and back)

## Problem 13: Push to GitHub and submit the URL

**Prompt:**

> Problem 13: Push to GitHub and submit the URL. Ok it's asking us to put our code in hw4 which we already have and push it to a public github repository. I believe I have one that you don't know about yet, right, or maybe you can see it from my other coursework in the main folder. I know you know this but we should not put our real .env file, the database dile, or product images in the github repository. We should use .gitignore and include a .env.example with placeholders only. Make a README.md that explains how to run the front end and back end after placing the data pack. I need the repo URL to submit to canvas for this class
