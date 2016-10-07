# Esola

Esola is a esoteric programming language.
Pronounced like "ebola"


## Node

Nodes are base structures in the language.
Just arbitrary alphanumeric string (must start with alpha).
For example:

    A
    C
    ABC
    Test42

Node may contain data, maximum 64bit value.
Initial value is zero.


## Connections

Everything is a connection between nodes.

In base level connection from A to B can be represented as:

   A -> B

One can easily make a loop:

   A -> B
   B -> A

Or more complex structures:

    A -> B
    A -> D
    A -> F
    B -> C
    D -> E
    C -> E
    F -> E

Same as a graph (if that makes any more sense):

    A--->B-->C
    |        |
    |\       V
    | -->F-->E
    V        ^
    D--------|


Connections are definitions, and permanent.

## Inputs

Connections itself are boring, unless you can do something with them.
Let's introduce inputs.

    'A' -> A
    125 -> B
    -123 -> C
    0x42 -> D

Simple as it is, input is special case of connection.
Actually input is just feeding data to node.
Input happens only once.

When node has data, it may output it immediately to it's connections.
Node itself keeps it's data until new data is feeded, or node is grounded.

 XXX If there's more data coming to node, those feedings are blocked until current data is gone.


## Outputs

Node can output data, usually `stdout` or `stderr`, which are special node names.

    A -> stdout
    'B' -> stdout

Since data in node can be in any format, simple formatters are supported:

    # Basic numeric representation, permanent connection
    A -> stdout

    # Basic numeric representation, one time connection
    A --> stdout

    # Character representation of lowest 8 bits
    A -!> stdout

Output connection is not permanent, but one time.

## Combined connections

When to connections combine, different handlers are available.
Queue is the default method:

    'A' -> A
    'B' -> A
    'C' -> A

These are just queued and once A value is outputted somewhere they are applied in order.
One can however change behaviour to "summing":

    1 -+> A
    2 -+> A
    5 -+> A

Value of node "A" will be `1 + 2 + 5 = 8`
Another useful feature is mul and divide:

    2 -*> A
    2 -/> A

Minus operation is not supported.

Combined connections are not permanent.

# Blocks

Of course we support blocks.
Block is a set of connections, which are logically in same group.
One could explain this as a method, but it's called for every input separately, saving it's state.


    {average
    # `in` is reserved keyword in collection
    in -+> A
    1 -+> N
    A -> R
    N -/> R
    <- R
    }

So syntax is: `@COLLECTION_NAME` and everything until `@@` will be included to the collection.
Collection names are globally available.

Example usage:

    1 -> average
    6 -> average
    9 -> average
    10 -> average
    average --> stdout

Output would be `6`.

One can reset collection at any time with `ground` operator:

    1 -> average
    6 -> average
    9 -> average
    10 -> average
    average --> stdout

    # Ground
    average -|>

    9 -> average
    10 -> average
    average -> stdout

Output would be:

    6
    9

## Comments and white space

Comment is marked with hash `#` and lasts until end of line.
Only one experssion per line.
White space is insignificant otherwise.
