import textwrap

import factory

from .models import CodeSample

from users.factories import UserFactory


class CodeSampleFactory(factory.DjangoModelFactory):

    class Meta:
        model = CodeSample
        django_get_or_create = ('code',)

    creator = factory.SubFactory(UserFactory)
    code = factory.Faker('sentence', nb_words=10)
    code_markup_type = 'html'
    copy = factory.Faker('sentence', nb_words=10)
    copy_markup_type = 'html'
    is_published = True


def initial_data():
    code_samples = [
        (
            """\
            <pre><code><span class=\"comment\"># Simple output (with Unicode)</span>
            >>> print(\"Hello, I'm Python!\")
            <span class=\"output\">Hello, I'm Python!</span>

            <span class=\"comment\"># Input, assignment</span>
            >>> name = input('What is your name?\\n')
            >>> print('Hi, %s.' % name)
            <span class=\"output\">What is your name?
            Python
            Hi, Python.</span></code>
            </pre>
            """,
            """\
            <h1>Quick &amp; Easy to Learn</h1>
            <p>Experienced programmers in any other language can pick up Python very
            quickly, and beginners find the clean syntax and indentation structure
            easy to learn.
            <a href=\"https://docs.python.org/3/tutorial/\">Whet your appetite</a>
            with our Python overview.</p>
            """
        ),
        (
            """\
            <pre><code><span class=\"comment\"># Simple arithmetic</span>
            >>> 1 / 2
            <span class=\"output\">0.5</span>
            >>> 2 ** 3
            <span class=\"output\">8</span>
            >>> 17 / 3  <span class=\"comment\"># true division returns a float</span>
            <span class=\"output\">5.666666666666667</span>
            >>> 17 // 3  <span class=\"comment\"># floor division</span>
            <span class=\"output\">5</span></code></pre>
            """,
            """\
            <h1>Intuitive Interpretation</h1>
            <p>Calculations are simple with Python, and expression syntax is
            straightforward: the operators <code>+</code>, <code>-</code>,
            <code>*</code> and <code>/</code> work as expected; parentheses
            <code>()</code> can be used for grouping.
            <a href=\"https://docs.python.org/3/tutorial/introduction.html
            #using-python-as-a-calculator\">More about simple math functions</a>.
            </p>
            """
        ),
        (
            """\
            <pre><code><span class=\"comment\"># List comprehensions</span>
            >>> fruits = ['Banana', 'Apple', 'Lime']
            >>> loud_fruits = [fruit.upper() for fruit in fruits]
            >>> print(loud_fruits)
            <span class=\"output\">['BANANA', 'APPLE', 'LIME']</span>

            <span class=\"comment\"># List and the enumerate function</span>
            >>> list(enumerate(fruits))
            <span class=\"output\">[(0, 'Banana'), (1, 'Apple'), (2, 'Lime')]</span></code></pre>
            """,
            """\
            <h1>Compound Data Types</h1>
            <p>Lists (known as arrays in other languages) are one of the
            compound data types that Python understands. Lists can be indexed,
            sliced and manipulated with other built-in functions.
            <a href=\"https://docs.python.org/3/tutorial/introduction.html
            #lists\">More about lists</a></p>
            """
        ),
        (
            """\
            <pre>
            <code>
            <span class=\"comment\"># For loop on a list</span>
            >>> numbers = [2, 4, 6, 8]
            >>> product = 1
            >>> for number in numbers:
            ...     product = product * number
            ...
            >>> print('The product is:', product)
            <span class=\"output\">The product is: 384</span>
            </code>
            </pre>
            """,
            """\
            <h1>All the Flow You&rsquo;d Expect</h1>
            <p>Python knows the usual control flow statements that other
            languages speak &mdash; <code>if</code>, <code>for</code>,
            <code>while</code> and <code>range</code> &mdash; with some of
            its own twists, of course.
            <a href=\"https://docs.python.org/3/tutorial/controlflow.html\">
            More control flow tools</a></p>
            """
        ),
        (
            """\
            <pre>
            <code>
            <span class=\"comment\"># Write Fibonacci series up to n</span>
            >>> def fib(n):
            >>>     a, b = 0, 1
            >>>     while a &lt; n:
            >>>         print(a, end=' ')
            >>>         a, b = b, a+b
            >>>     print()
            >>> fib(1000)
            <span class=\"output\">0 1 1 2 3 5 8 13 21 34 55 89 144 233 377 610</span>
            </code>
            </pre>
            """,
            """\
            <h1>Functions Defined</h1>
            <p>The core of extensible programming is defining functions.
            Python allows mandatory and optional arguments, keyword arguments,
            and even arbitrary argument lists.
            <a href=\"https://docs.python.org/3/tutorial/controlflow.html
            #defining-functions\">More about defining functions</a></p>
            """
        ),
    ]
    return {
        'boxes': [
            CodeSampleFactory(
                code=textwrap.dedent(code), copy=textwrap.dedent(copy),
            ) for code, copy in code_samples
        ],
    }
