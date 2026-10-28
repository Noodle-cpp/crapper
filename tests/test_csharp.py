from pathlib import Path

from crapper.discover import is_generated_source, is_test_file, language_of
from crapper.languages.csharp import functions_in_source

SCORE = """
class Sample {
    int score(bool a, bool b, int[] values) {
        for (int i = 0; i < values.Length; i++) {
        }
        foreach (int value in values) {
        }
        while (a) {
            a = false;
        }
        do {
            b = false;
        } while (b);
        if (a && b || values.Length > 0) {
        }
        try {
            return a ? 1 : 0;
        } catch (System.Exception ex) {
            return 2;
        }
    }
}
"""

NESTED = """
class Sample {
    int nested(bool a, bool b, int[] values) {
        for (int i = 0; i < values.Length; i++) {
            if (a) {
            }
        }
        foreach (int value in values) {
            if (b) {
            }
        }
        while (a) {
            if (b) {
            }
            a = false;
        }
        do {
            if (a) {
            }
            b = false;
        } while (b);
        try {
            return a ? (b ? 1 : 0) : 2;
        } catch (System.Exception ex) {
            if (values.Length > 0) {
                return values[0];
            }
            return 3;
        }
    }

    int switched(int value) {
        switch (value) {
            case 1:
                if (value > 0) {
                    return 1;
                }
                return 0;
            default:
                return 2;
        }
    }
}
"""

LAMBDA = """
class Sample {
    int outer() {
        System.Action runnable = () => {
            if (true) {
            }
        };
        return 1;
    }
}
"""


def test_counts_the_same_decisions_as_java():
    methods = functions_in_source(SCORE, "Sample.cs")
    assert [(method.name, method.complexity) for method in methods] == [("score", 10)]

    methods = functions_in_source(NESTED, "Sample.cs")
    assert [(method.name, method.complexity) for method in methods] == [
        ("nested", 13),
        ("switched", 4),
    ]


def test_lambda_bodies_are_not_entries_and_do_not_raise_complexity():
    methods = functions_in_source(LAMBDA, "Sample.cs")
    assert [(method.name, method.complexity) for method in methods] == [("outer", 1)]


def test_ignores_constructors_and_names_types_for_uml_viewer():
    source = """
    namespace demo.pkg;
    public class Board {
        Board() { if (true) {} }
        public void Place(int x) { if (x > 0 && ready) return; }
        class Inner { void Tick() { return; } }
    }
    """
    methods = functions_in_source(source, "src/demo/pkg/Board.cs")
    assert [(method.namespace, method.name, method.complexity) for method in methods] == [
        ("demo.pkg.Board", "Place", 3),
        ("demo.pkg.Board.Inner", "Tick", 1),
    ]
    assert methods[0].jacoco_class == "demo.pkg.Board"
    assert methods[1].jacoco_class == "demo.pkg.Board+Inner"


def test_expression_bodied_method_is_scored():
    source = """
    class Sample {
        int Arrow(bool a) => a ? 1 : 0;
    }
    """
    methods = functions_in_source(source, "Sample.cs")
    assert [(method.name, method.complexity) for method in methods] == [("Arrow", 2)]


def test_property_accessors_are_not_entries():
    source = """
    class Sample {
        public int P {
            get { if (true) { return 1; } return 0; }
            set { if (value > 0) { } }
        }
        void Work() { return; }
    }
    """
    methods = functions_in_source(source, "Sample.cs")
    assert [(method.name, method.complexity) for method in methods] == [("Work", 1)]


def test_keywords_in_comments_and_strings_are_not_decisions():
    source = """
    class Sample {
        int Stable() {
            string text = "if && || ? case default catch";
            // if && || ? case default catch
            /* if && || ? case default catch */
            return 1;
        }
    }
    """
    methods = functions_in_source(source, "Sample.cs")
    assert [(method.name, method.complexity) for method in methods] == [("Stable", 1)]


def test_discover_skips_generated_and_test_csharp():
    assert language_of("Board.cs") == "csharp"
    assert is_generated_source("Form.Designer.cs")
    assert is_test_file("BoardTests.cs")
    assert is_test_file("My.App.Tests/GlpiTestHttp.cs")
    assert not is_test_file("BoardTestHelper.cs")
