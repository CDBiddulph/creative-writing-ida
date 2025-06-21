# Transcripts of our "delegated microfiction" experiments

The following are transcripts from an experiment conducted at the MIT Media Lab exploring creative delegation under extreme time pressure, as part of our paper, *Scaffolded Creativity: Distributed Storytelling via Hierarchical Time-Constrained Collaboration*. In this setup, writers were asked to compose complete microfiction stories, but with a twist: they could delegate subtasks — such as brainstorming ideas, drafting stories, or rewriting endings — to a team of humans organized in a tree-like structure.

Each node in the tree had limited context and time, and communication flowed only downward. Writers at the top made rapid decisions, often based on fragmented input from below.

Each top-level writer had a total of 10 minutes to work, not including time spent waiting for a response from their collaborators. To minimize downtime, we automatically assigned writers to a new or partially-completed task from a queue as soon as they requested help from collaborators; once the response was ready, we put the task back in the same top-level writer's queue. All submissions (whether intermediate or final) were limited to 2,500 characters or less.

While writers with many levels of experience were involved in this experiment, all of the top-level writers in the transcripts below were drawn from our pool of professional authors.

LLMs were not involved in these experiments; however, the dynamics uncovered here have implications for the future of human-AI collaboration. As language models become increasingly integrated into creative workflows, understanding how humans naturally decompose and delegate creative tasks can inform the design of more intuitive and aligned AI systems. By observing how ideas evolve through constrained, hierarchical communication, we can better anticipate both the strengths and bottlenecks in distributed storytelling — whether the collaborators are humans, machines, or a hybrid of both.

## About the Transcript Format

Each transcript is structured as an XML-like document containing the prompts and submissions within one session:

* `<sessions>` is the root node.
* `<session>` wraps the entire exchange for one <prompt> and <submit> of a top-level writer.
* `<prompt>` contains the initial writing instruction or challenge given to the top-level writer.
* `<submit>` contains a finalized submission that the writer compiles, often integrating or building on delegated responses.

In these transcripts, we omit all intermediate `<ask>`, `<response>`, and `<notes>` tags, focusing instead on the completed output in relation to the original challenge. See `full_transcripts.md` for the longer transcripts which contain these tags.
