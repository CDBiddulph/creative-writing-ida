from src.session_xml_generator.session_xml_generator import SessionXmlGenerator


class ClaudeChatSessionXmlGenerator(SessionXmlGenerator):
    """Generate sessions in XML format using Claude Chat model."""

    def generate_leaf(self, prompt: str) -> str:
        pass

    def generate_parent(self, prompt: str) -> str:
        pass
