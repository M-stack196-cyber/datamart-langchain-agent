import {
  ArrowRight,
  Bot,
  BrainCircuit,
  Check,
  ChevronDown,
  Code2,
  Database,
  Menu,
  Rocket,
  ShieldCheck,
  Sparkles,
  Users,
  Wrench,
  X,
} from "lucide-react";
import { useState } from "react";


const services = [
  {
    icon: <Users size={26} />,
    title: "Staff Augmentation",
    description:
      "Add experienced engineers directly to your existing development workflow.",
    points: [
      "Fast developer placement",
      "Pre-vetted senior talent",
      "Flexible engagement",
    ],
  },
  {
    icon: <Rocket size={26} />,
    title: "MVP Development",
    description:
      "Turn your product idea into a production-ready application with an experienced engineering team.",
    points: [
      "Product strategy",
      "Design & development",
      "Full code ownership",
    ],
  },
  {
    icon: <BrainCircuit size={26} />,
    title: "AI & Automation",
    description:
      "Build intelligent AI agents, RAG systems, LLM applications and automated business workflows.",
    points: [
      "Agentic AI",
      "LLM & RAG systems",
      "Workflow automation",
    ],
  },
  {
    icon: <Wrench size={26} />,
    title: "SaaS Maintenance",
    description:
      "Keep existing software reliable, secure, performant and continuously improving.",
    points: [
      "Ongoing support",
      "Security updates",
      "Performance optimization",
    ],
  },
  {
    icon: <Database size={26} />,
    title: "Odoo ERP Solutions",
    description:
      "Bring disconnected business operations into one integrated and customized ERP platform.",
    points: [
      "Custom modules",
      "Migration",
      "Training & support",
    ],
  },
];


const technologies = [
  "Agentic AI",
  "LLMs & RAG",
  "React",
  "Node.js",
  "Python",
  "Ruby on Rails",
  "SaaS Architecture",
  ".NET / C#",
  "PostgreSQL",
  "MongoDB",
  "AWS",
  "Docker & Kubernetes",
  "TypeScript",
  "Flutter",
  "React Native",
  "OpenAI / GPT",
  "LangChain",
  "CI/CD Pipelines",
];


const faqs = [
  "How quickly can Datamart add a developer to my team?",
  "How long does it take to build an MVP?",
  "What does staff augmentation cost?",
  "What is the minimum project size?",
  "Which technologies does Datamart specialize in?",
  "Where is Datamart located?",
  "Do you provide ongoing maintenance and support?",
  "How do communication and project management work?",
];


export default function DtmHomepage({ onOpenChat }) {
  const [mobileMenu, setMobileMenu] = useState(false);
  const [openFaq, setOpenFaq] = useState(null);

  return (
    <div className="dtm-site">

      {/* NAVBAR */}
      <header className="dtm-navbar">
        <div className="dtm-container dtm-nav-inner">
          <a className="dtm-logo" href="#top">
            <span className="dtm-logo-mark">D</span>
            <span>Datamart</span>
          </a>

          <nav className="dtm-desktop-nav">
            <a href="#services">Services</a>
            <a href="#work">Our Work</a>
            <a href="#industries">Industries</a>
            <a href="#technology">Technology</a>
            <a href="#about">About</a>
          </nav>

          <div className="dtm-nav-actions">
            <button
              className="dtm-nav-chat"
              type="button"
              onClick={onOpenChat}
            >
              <Bot size={17} />
              Ask AI
            </button>

            <a className="dtm-button dtm-button-dark" href="#contact">
              Get Started
              <ArrowRight size={17} />
            </a>

            <button
              className="dtm-mobile-toggle"
              type="button"
              onClick={() => setMobileMenu((value) => !value)}
              aria-label="Toggle navigation"
            >
              {mobileMenu ? <X /> : <Menu />}
            </button>
          </div>
        </div>

        {mobileMenu && (
          <div className="dtm-mobile-menu">
            <a href="#services">Services</a>
            <a href="#work">Our Work</a>
            <a href="#industries">Industries</a>
            <a href="#technology">Technology</a>
            <a href="#about">About</a>
          </div>
        )}
      </header>


      <main id="top">

        {/* HERO */}
        <section className="dtm-hero">
          <div className="dtm-container dtm-hero-grid">
            <div className="dtm-hero-copy">
              <div className="dtm-eyebrow">
                <Sparkles size={16} />
                Trusted engineering partner since 2011
              </div>

              <h1>
                Your Engineering Team,
                <span> Without the Hiring Bottleneck</span>
              </h1>

              <p>
                Scale software delivery with experienced engineers,
                product teams and AI specialists who integrate directly
                into your workflow.
              </p>

              <div className="dtm-hero-actions">
                <a className="dtm-button dtm-button-primary" href="#contact">
                  Get a Free Technical Audit
                  <ArrowRight size={18} />
                </a>

                <a className="dtm-button dtm-button-outline" href="#work">
                  See Our Case Studies
                </a>
              </div>

              <div className="dtm-hero-stats">
                <div>
                  <strong>150+</strong>
                  <span>Projects Delivered</span>
                </div>
                <div>
                  <strong>15+</strong>
                  <span>Years Experience</span>
                </div>
                <div>
                  <strong>50+</strong>
                  <span>Happy Clients</span>
                </div>
              </div>
            </div>

            <div className="dtm-hero-visual">
              <div className="dtm-code-card">
                <div className="dtm-code-top">
                  <span />
                  <span />
                  <span />
                </div>

                <div className="dtm-code-icon">
                  <Code2 size={46} />
                </div>

                <p>Engineering. AI. Product.</p>

                <div className="dtm-floating-card card-one">
                  <ShieldCheck size={21} />
                  <span>US Managed</span>
                </div>

                <div className="dtm-floating-card card-two">
                  <Sparkles size={21} />
                  <span>AI Enabled</span>
                </div>
              </div>
            </div>
          </div>
        </section>


        {/* CLIENT LOGOS */}
        <section className="dtm-trusted">
          <div className="dtm-container">
            <p className="dtm-section-kicker">
              Powering innovation for world-class companies
            </p>

            <div className="dtm-logo-row">
              {[
                "HeartFlow",
                "Acxiom",
                "Scalr",
                "Cardinal Path",
                "Ensighten",
                "Enreach",
                "ScreenMeet",
              ].map((company) => (
                <span key={company}>{company}</span>
              ))}
            </div>
          </div>
        </section>


        {/* PROBLEM */}
        <section className="dtm-section dtm-problem">
          <div className="dtm-container">
            <span className="dtm-label">The Problem</span>
            <h2>Sound Familiar?</h2>
            <p className="dtm-section-intro">
              Growing companies often hit the same engineering
              bottlenecks.
            </p>

            <div className="dtm-four-grid">
              {[
                ["Can't Hire Fast Enough", "Critical engineering roles stay open while the roadmap keeps moving."],
                ["No Technical Co-Founder", "You have the product vision but need the technical team to execute it."],
                ["Manual Everything", "Important business processes still depend on spreadsheets and repetitive work."],
                ["No One Maintaining Your Product", "Legacy systems become harder, slower and riskier to operate."],
              ].map(([title, copy], index) => (
                <article className="dtm-problem-card" key={title}>
                  <span className="dtm-card-number">
                    0{index + 1}
                  </span>
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>


        {/* WHY DATAMART */}
        <section className="dtm-section dtm-why" id="about">
          <div className="dtm-container">
            <div className="dtm-split-heading">
              <div>
                <span className="dtm-label">Why Datamart</span>
                <h2>The Hiring Problem Is Solved.</h2>
              </div>

              <p>
                Datamart gives companies a faster way to access
                experienced engineering talent without building an
                entire recruitment operation.
              </p>
            </div>

            <div className="dtm-four-grid">
              {[
                ["US-Managed, Globally Delivered", "Strategy and client management combined with a global engineering delivery team."],
                ["Lower Engineering Cost", "Scale software capacity without the overhead of traditional local hiring."],
                ["Real-Time Collaboration", "Engineers work inside your existing tools, standups and development workflow."],
                ["Long-Term Experience", "Years of experience delivering products for startups, SaaS companies and enterprises."],
              ].map(([title, copy]) => (
                <article className="dtm-feature-card" key={title}>
                  <div className="dtm-feature-icon">
                    <Check size={19} />
                  </div>
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>


        {/* SERVICES */}
        <section className="dtm-section dtm-services" id="services">
          <div className="dtm-container">
            <span className="dtm-label">What We Do</span>
            <h2>Five Ways We Work With You</h2>
            <p className="dtm-section-intro">
              From adding engineering capacity to building complete
              products and AI systems.
            </p>

            <div className="dtm-services-grid">
              {services.map((service) => (
                <article className="dtm-service-card" key={service.title}>
                  <div className="dtm-service-icon">{service.icon}</div>
                  <h3>{service.title}</h3>
                  <p>{service.description}</p>

                  <ul>
                    {service.points.map((point) => (
                      <li key={point}>
                        <Check size={15} />
                        {point}
                      </li>
                    ))}
                  </ul>

                  <a href="#contact">
                    Learn more
                    <ArrowRight size={16} />
                  </a>
                </article>
              ))}
            </div>
          </div>
        </section>


        {/* CASE STUDIES */}
        <section className="dtm-section dtm-work" id="work">
          <div className="dtm-container">
            <div className="dtm-split-heading">
              <div>
                <span className="dtm-label">Case Studies</span>
                <h2>Proven Results, Real Impact</h2>
              </div>

              <a href="#contact" className="dtm-text-link">
                View All Case Studies
                <ArrowRight size={17} />
              </a>
            </div>

            <div className="dtm-case-grid">
              {[
                ["Analytics", "Woopra Mobile SDK Modernization", "60% Faster Performance"],
                ["Healthcare", "AI Healthcare Platform", "99.99% Uptime"],
                ["SaaS", "Long-Term SaaS Partnership", "10x Scale"],
              ].map(([category, title, result]) => (
                <article className="dtm-case-card" key={title}>
                  <div className="dtm-case-image">
                    <span>{category}</span>
                  </div>
                  <div className="dtm-case-content">
                    <small>{category}</small>
                    <h3>{title}</h3>
                    <strong>{result}</strong>
                    <a href="#contact">
                      Read Case Study
                      <ArrowRight size={16} />
                    </a>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>


        {/* DATAMART LABS */}
        <section className="dtm-section dtm-labs">
          <div className="dtm-container dtm-labs-grid">
            <div>
              <span className="dtm-label">Datamart Labs</span>
              <h2>We Build What We Sell.</h2>
              <p>
                Alongside client work, Datamart develops internal
                software products, giving our teams first-hand product
                building and scaling experience.
              </p>

              <a className="dtm-button dtm-button-light" href="#contact">
                Discuss Your Project
                <ArrowRight size={17} />
              </a>
            </div>

            <article className="dtm-labs-card">
              <small>Internal Venture</small>
              <h3>RubyOrbit</h3>
              <p>
                AI-powered revenue intelligence designed to score
                leads and generate tactical sales insights.
              </p>

              <div className="dtm-tag-row">
                <span>AI Lead Scoring</span>
                <span>Action Signals</span>
                <span>LLM Playbooks</span>
              </div>
            </article>
          </div>
        </section>


        {/* INDUSTRIES / RESULTS */}
        <section className="dtm-section" id="industries">
          <div className="dtm-container">
            <span className="dtm-label">Results</span>
            <h2>Engineering That Moves the Business</h2>

            <div className="dtm-results-grid">
              {[
                ["99.99%", "Platform Uptime", "Reliable software systems built for critical workloads."],
                ["4,000%", "First-Year ROI", "Modern digital products designed around measurable outcomes."],
                ["2x", "Pipeline Throughput", "Faster platforms through focused engineering and optimization."],
                ["1-2 wk", "Developer Placement", "Experienced engineers embedded without lengthy hiring cycles."],
              ].map(([value, label, copy]) => (
                <article key={label}>
                  <strong>{value}</strong>
                  <h3>{label}</h3>
                  <p>{copy}</p>
                </article>
              ))}
            </div>
          </div>
        </section>


        {/* TECHNOLOGY */}
        <section className="dtm-section dtm-tech" id="technology">
          <div className="dtm-container">
            <span className="dtm-label">Technology</span>
            <h2>Our Expertise, Your Competitive Edge</h2>
            <p className="dtm-section-intro">
              Modern AI, cloud, web and mobile technologies for
              production software.
            </p>

            <div className="dtm-tech-cloud">
              {technologies.map((technology) => (
                <span key={technology}>{technology}</span>
              ))}
            </div>

            <button
              type="button"
              className="dtm-button dtm-button-primary"
              onClick={onOpenChat}
            >
              <Bot size={17} />
              Ask Our AI Assistant
            </button>
          </div>
        </section>


        {/* FAQ */}
        <section className="dtm-section dtm-faq">
          <div className="dtm-container">
            <span className="dtm-label">FAQ</span>
            <h2>Frequently Asked Questions</h2>

            <div className="dtm-faq-list">
              {faqs.map((question, index) => (
                <button
                  type="button"
                  className={`dtm-faq-item ${
                    openFaq === index ? "open" : ""
                  }`}
                  key={question}
                  onClick={() =>
                    setOpenFaq(openFaq === index ? null : index)
                  }
                >
                  <div>
                    <strong>{question}</strong>
                    <ChevronDown size={20} />
                  </div>

                  {openFaq === index && (
                    <p>
                      Our team can provide a recommendation based on
                      your project, timeline, technical requirements
                      and engineering capacity. Use the AI assistant
                      or contact Datamart for details.
                    </p>
                  )}
                </button>
              ))}
            </div>
          </div>
        </section>


        {/* FINAL CTA */}
        <section className="dtm-final-cta" id="contact">
          <div className="dtm-container">
            <div className="dtm-cta-card">
              <span className="dtm-label">Ready to move faster?</span>
              <h2>Build. Scale. Transform.</h2>

              <p>
                Add engineering capacity, launch your next product or
                automate manual workflows with Datamart.
              </p>

              <div className="dtm-hero-actions">
                <a className="dtm-button dtm-button-light" href="mailto:hello@dtm.io">
                  Book a Free Technical Audit
                  <ArrowRight size={17} />
                </a>

                <button
                  className="dtm-button dtm-button-transparent"
                  type="button"
                  onClick={onOpenChat}
                >
                  <Bot size={17} />
                  Chat With Datamart AI
                </button>
              </div>
            </div>
          </div>
        </section>

      </main>


      {/* FOOTER */}
      <footer className="dtm-footer">
        <div className="dtm-container dtm-footer-grid">
          <div>
            <a className="dtm-logo dtm-footer-logo" href="#top">
              <span className="dtm-logo-mark">D</span>
              <span>Datamart Inc</span>
            </a>

            <p>
              Software engineering, staff augmentation, AI automation
              and product development.
            </p>
          </div>

          <div>
            <strong>Services</strong>
            <a href="#services">Staff Augmentation</a>
            <a href="#services">MVP Development</a>
            <a href="#services">AI & Automation</a>
            <a href="#services">SaaS Maintenance</a>
          </div>

          <div>
            <strong>Company</strong>
            <a href="#work">Case Studies</a>
            <a href="#about">About</a>
            <a href="#technology">Technology</a>
            <a href="mailto:hello@dtm.io">Contact</a>
          </div>

          <div>
            <strong>Contact</strong>
            <span>Palo Alto, California</span>
            <a href="mailto:hello@dtm.io">hello@dtm.io</a>
          </div>
        </div>

        <div className="dtm-container dtm-footer-bottom">
          <span>© 2026 Datamart Inc.</span>
          <span>Engineering • AI • Product</span>
        </div>
      </footer>
    </div>
  );
}
