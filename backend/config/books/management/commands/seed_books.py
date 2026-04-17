from django.core.management.base import BaseCommand
from books.models import Book
from books.rag import add_to_vector_db


BOOKS = [
    ("Atomic Habits", "James Clear", 4.8, "https://jamesclear.com/atomic-habits", "A practical guide to behavior design that explains how tiny, consistent changes compound into remarkable results. It introduces cues, cravings, responses, and rewards as the core habit loop."),
    ("Deep Work", "Cal Newport", 4.7, "https://www.calnewport.com/books/deep-work/", "A productivity framework for focused, distraction-free work. It contrasts shallow tasks with cognitively demanding work and offers rituals to improve concentration."),
    ("Clean Code", "Robert C. Martin", 4.7, "https://www.oreilly.com/library/view/clean-code/9780136083238/", "A software craftsmanship classic covering readable naming, function design, testing discipline, and refactoring strategies for maintainable code."),
    ("The Pragmatic Programmer", "Andrew Hunt & David Thomas", 4.8, "https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/", "A handbook for software developers with timeless principles like ownership, automation, continuous learning, and practical architecture decisions."),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", 4.9, "https://dataintensive.net/", "A deep dive into data systems covering storage engines, indexing, replication, partitioning, consistency, stream processing, and reliability trade-offs."),
    ("The Psychology of Money", "Morgan Housel", 4.6, "https://www.morganhousel.com/the-psychology-of-money/", "Explains how behavior and emotions shape financial outcomes more than technical knowledge. It highlights compounding, risk, and long-term thinking."),
    ("Sapiens", "Yuval Noah Harari", 4.7, "https://www.ynharari.com/book/sapiens-2/", "A macro-history of humankind from cognitive evolution to modern institutions, exploring myths, agriculture, empires, and scientific revolutions."),
    ("Homo Deus", "Yuval Noah Harari", 4.5, "https://www.ynharari.com/book/homo-deus/", "A future-facing analysis of technology, AI, and biotech, discussing how human priorities might shift from survival toward enhancement and control."),
    ("The Alchemist", "Paulo Coelho", 4.4, "https://www.harpercollins.com/products/the-alchemist-paulo-coelho", "A philosophical fiction about purpose and destiny through the journey of a shepherd who follows his recurring dream toward a hidden treasure."),
    ("To Kill a Mockingbird", "Harper Lee", 4.8, "https://www.harpercollins.com/products/to-kill-a-mockingbird-harper-lee", "A coming-of-age legal drama examining justice, prejudice, and moral courage in a small town through the perspective of Scout Finch."),
    ("1984", "George Orwell", 4.7, "https://www.penguin.co.uk/books/171645/1984-by-orwell-george/9780141036144", "A dystopian political novel about surveillance, propaganda, and language manipulation under an authoritarian regime."),
    ("Brave New World", "Aldous Huxley", 4.5, "https://www.harpercollins.com/products/brave-new-world-aldous-huxley", "A dystopia where engineered comfort replaces freedom and individuality. It explores social conditioning, pleasure, and control."),
    ("The Great Gatsby", "F. Scott Fitzgerald", 4.4, "https://www.penguinrandomhouse.com/books/589886/the-great-gatsby-by-f-scott-fitzgerald/", "A critique of wealth, aspiration, and illusion in Jazz Age America through the story of Jay Gatsby and his obsession with the past."),
    ("The Hobbit", "J.R.R. Tolkien", 4.8, "https://www.harpercollins.com/products/the-hobbit-jrr-tolkien", "A fantasy adventure that follows Bilbo Baggins on a quest involving dwarves, dragons, and personal transformation."),
    ("The Lord of the Rings", "J.R.R. Tolkien", 4.9, "https://www.harpercollins.com/products/the-lord-of-the-rings-jrr-tolkien", "An epic fantasy about friendship, sacrifice, and power as diverse allies attempt to destroy a corrupting ring."),
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", 4.8, "https://www.bloomsbury.com/uk/harry-potter-and-the-philosophers-stone-9781408855652/", "A magical school story introducing Harry Potter, friendship, and the conflict between courage and fear."),
    ("The Name of the Wind", "Patrick Rothfuss", 4.7, "https://www.penguinrandomhouse.com/books/295118/the-name-of-the-wind-by-patrick-rothfuss/", "A lyrical fantasy memoir told by a legendary figure, covering music, magic, learning, and myth."),
    ("Dune", "Frank Herbert", 4.8, "https://www.penguinrandomhouse.com/books/352036/dune-by-frank-herbert/", "A science-fiction saga about ecology, power, prophecy, and survival on a desert planet central to galactic politics."),
    ("Foundation", "Isaac Asimov", 4.6, "https://www.penguinrandomhouse.com/books/295807/foundation-by-isaac-asimov/", "A science-fiction classic where psychohistory predicts civilizational collapse and guides a plan to shorten the coming dark age."),
    ("Project Hail Mary", "Andy Weir", 4.8, "https://www.penguinrandomhouse.com/books/611416/project-hail-mary-by-andy-weir/", "A fast-paced sci-fi mission blending humor, scientific problem solving, and unexpected friendship to save Earth."),
    ("The Martian", "Andy Weir", 4.7, "https://www.penguinrandomhouse.com/books/222677/the-martian-by-andy-weir/", "An engineer stranded on Mars survives through systems thinking, creativity, and relentless experimentation."),
    ("Thinking, Fast and Slow", "Daniel Kahneman", 4.6, "https://us.macmillan.com/books/9780374533557/thinkingfastandslow", "A cognitive science overview of two thinking modes, heuristics, biases, and decision quality."),
    ("Influence", "Robert B. Cialdini", 4.6, "https://www.harpercollins.com/products/influence-new-and-expanded-robert-b-cialdini", "A psychology and persuasion framework built around principles like reciprocity, social proof, authority, and scarcity."),
    ("Start With Why", "Simon Sinek", 4.5, "https://www.penguinrandomhouse.com/books/304736/start-with-why-by-simon-sinek/", "Leadership and communication insights focused on purpose-first messaging and mission-driven organizations."),
    ("Zero to One", "Peter Thiel", 4.4, "https://www.penguinrandomhouse.com/books/222113/zero-to-one-by-peter-thiel-with-blake-masters/", "Startup strategy focused on creating monopolistic value through innovation rather than incremental competition."),
    ("Rework", "Jason Fried & David Heinemeier Hansson", 4.3, "https://basecamp.com/books/rework", "A contrarian guide to building products and companies with less complexity, fewer meetings, and clearer priorities."),
    ("Hooked", "Nir Eyal", 4.3, "https://www.nirandfar.com/hooked/", "A product design framework for habit-forming experiences based on trigger, action, variable reward, and investment."),
    ("The Lean Startup", "Eric Ries", 4.5, "https://theleanstartup.com/book", "A startup methodology centered on rapid experimentation, validated learning, and iterative product-market fit discovery."),
    ("The Hard Thing About Hard Things", "Ben Horowitz", 4.6, "https://a16z.com/book/the-hard-thing-about-hard-things/", "Candid lessons on leadership during crises, hiring decisions, culture, and tough execution trade-offs."),
    ("Can't Hurt Me", "David Goggins", 4.7, "https://www.lioncrest.com/books/cant-hurt-me", "A memoir and mindset guide emphasizing accountability, resilience, and disciplined discomfort."),
    ("Ikigai", "Hector Garcia & Francesc Miralles", 4.4, "https://www.penguin.co.uk/books/111/1112961/ikigai/9781786330895.html", "A lifestyle exploration of purpose, longevity, and daily routines inspired by Japanese well-being practices."),
    ("Rich Dad Poor Dad", "Robert T. Kiyosaki", 4.3, "https://www.richdad.com", "An introduction to financial mindset, asset-building, and income perspectives through contrasting role models."),
    ("The Intelligent Investor", "Benjamin Graham", 4.7, "https://www.harpercollins.com/products/the-intelligent-investor-rev-ed-benjamin-graham", "A foundational investing book on value investing, margin of safety, and long-term risk management."),
    ("A Brief History of Time", "Stephen Hawking", 4.5, "https://www.penguinrandomhouse.com/books/212068/a-brief-history-of-time-by-stephen-hawking/", "An accessible introduction to cosmology, black holes, relativity, and big-picture physics questions."),
    ("Cosmos", "Carl Sagan", 4.8, "https://www.penguinrandomhouse.com/books/159994/cosmos-by-carl-sagan/", "A poetic tour of the universe and scientific discovery, blending astronomy, history, and human curiosity."),
    ("The Selfish Gene", "Richard Dawkins", 4.5, "https://global.oup.com/academic/product/the-selfish-gene-9780192860927", "A genetics perspective on evolution focused on gene-centered selection and biological behavior."),
    ("The Gene", "Siddhartha Mukherjee", 4.6, "https://www.simonandschuster.com/books/The-Gene/Siddhartha-Mukherjee/9781476733524", "A narrative history of genetics, inheritance, ethics, and the scientific race to decode life."),
    ("Educated", "Tara Westover", 4.7, "https://www.penguinrandomhouse.com/books/550168/educated-by-tara-westover/", "A memoir of self-invention through education, resilience, and identity reconstruction."),
    ("Becoming", "Michelle Obama", 4.8, "https://www.penguinrandomhouse.com/books/549426/becoming-by-michelle-obama/", "A personal memoir about family, work, public service, and growth through changing responsibilities."),
    ("The Diary of a Young Girl", "Anne Frank", 4.8, "https://www.penguinrandomhouse.com/books/76846/the-diary-of-a-young-girl-by-anne-frank/", "A historic diary documenting hope, fear, and humanity during wartime persecution."),
]


class Command(BaseCommand):
    help = "Seed many high-quality books for demo and testing."

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for title, author, rating, url, description in BOOKS:
            obj, is_created = Book.objects.get_or_create(
                title=title,
                author=author,
                defaults={
                    "rating": rating,
                    "url": url,
                    "description": description,
                },
            )
            if is_created:
                created += 1
                add_to_vector_db(obj.id, obj.title, obj.description)
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f"Books created: {created}, skipped(existing): {skipped}"))
