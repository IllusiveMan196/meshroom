# coding:utf-8

from meshroom.core.graph import Graph, loadGraph
from meshroom.core import desc, registerNodeType, unregisterNodeType
from meshroom.core.node import Node


class NodeWithAttributeChangedCallback(desc.Node):
    """
    A Node containing an input Attribute with an 'on{Attribute}Changed' method,
    called whenever the value of this attribute is changed explicitly.
    """

    inputs = [
        desc.IntParam(
            name="input",
            label="Input",
            description="Attribute with a value changed callback (onInputChanged)",
            value=0,
            range=None,
        ),
        desc.IntParam(
            name="affectedInput",
            label="Affected Input",
            description="Updated to input.value * 2 whenever 'input' is explicitly modified",
            value=0,
            range=None,
        ),
    ]

    def onInputChanged(self, instance: Node):
        instance.affectedInput.value = instance.input.value * 2

    def processChunk(self, chunk):
        pass  # No-op.



class TestNodeWithAttributeChangedCallback:
    @classmethod
    def setup_class(cls):
        registerNodeType(NodeWithAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithAttributeChangedCallback)

    def test_assignValueTriggersCallback(self):
        node = Node(NodeWithAttributeChangedCallback.__name__)
        assert node.affectedInput.value == 0

        node.input.value = 10
        assert node.affectedInput.value == 20

    def test_specifyDefaultValueDoesNotTriggerCallback(self):
        node = Node(NodeWithAttributeChangedCallback.__name__, input=10)
        assert node.affectedInput.value == 0

    def test_assignDefaultValueDoesNotTriggerCallback(self):
        node = Node(NodeWithAttributeChangedCallback.__name__, input=10)
        node.input.value = 10
        assert node.affectedInput.value == 0

    def test_assignNonDefaultValueTriggersCallback(self):
        node = Node(NodeWithAttributeChangedCallback.__name__, input=10)
        node.input.value = 2
        assert node.affectedInput.value == 4


class TestAttributeCallbackTriggerInGraph:
    @classmethod
    def setup_class(cls):
        registerNodeType(NodeWithAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithAttributeChangedCallback)

    def test_connectionTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 0

        nodeA.input.value = 1
        graph.addEdge(nodeA.input, nodeB.input)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 2

    def test_connectedValueChangeTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 0

        graph.addEdge(nodeA.input, nodeB.input)
        nodeA.input.value = 1

        assert nodeA.affectedInput.value == 2
        assert nodeB.affectedInput.value == 2

    def test_defaultValueOnlyTriggersCallbackDownstream(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__, input=1)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == 0
        assert nodeB.affectedInput.value == 0

        graph.addEdge(nodeA.input, nodeB.input)

        assert nodeA.affectedInput.value == 0
        assert nodeB.affectedInput.value == 2

    def test_valueChangeIsPropagatedAlongNodeChain(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeC = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeD = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        graph.addEdges(
            (nodeA.affectedInput, nodeB.input),
            (nodeB.affectedInput, nodeC.input),
            (nodeC.affectedInput, nodeD.input),
        )

        nodeA.input.value = 5

        assert nodeA.affectedInput.value == nodeB.input.value == 10
        assert nodeB.affectedInput.value == nodeC.input.value == 20
        assert nodeC.affectedInput.value == nodeD.input.value == 40
        assert nodeD.affectedInput.value == 80

    def test_disconnectionTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        graph.addEdge(nodeA.input, nodeB.input)
        nodeA.input.value = 5
        assert nodeB.affectedInput.value == 10

        graph.removeEdge(nodeB.input)

        assert nodeB.input.value == 0
        assert nodeB.affectedInput.value == 0

    def test_loadingGraphDoesNotTriggerCallback(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        node.input.value = 5
        node.affectedInput.value = 2
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(node.name)
        assert loadedNode
        assert loadedNode.affectedInput.value == 2

    def test_loadingGraphDoesNotTriggerCallbackForConnectedAttributes(
        self, graphSavedOnDisk
    ):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        graph.addEdge(nodeA.input, nodeB.input)
        nodeA.input.value = 5
        nodeB.affectedInput.value = 2

        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNodeB = loadedGraph.node(nodeB.name)
        assert loadedNodeB
        assert loadedNodeB.affectedInput.value == 2

