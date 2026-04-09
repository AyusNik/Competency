"""Run once to seed sample data into MongoDB."""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "cat_db"

SAMPLE_TRAININGS = [
    {
        "name": "DSA - Arrays & Strings Training",
        "description": "Covers array manipulation, sliding window, two-pointer techniques.",
        "basic_groups": [
            {
                "group_name": "AttainBasic - Arrays",
                "requirement_grouping": "And",
                "items": [
                    {"courses": ["ARRAYS FUNDAMENTALS ONLINE TBT"], "min_requirements": 1},
                    {"courses": ["STRING MANIPULATION BASICS"], "min_requirements": 1},
                    {"courses": ["ARRAYS BASIC ASSESSMENT"], "min_requirements": 1},
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "AttainAdvanced - Arrays",
                "requirement_grouping": "And",
                "items": [
                    {
                        "courses": [
                            "SLIDING WINDOW TECHNIQUE", "TWO POINTER APPROACH",
                            "KADANE ALGORITHM DEEP DIVE", "PREFIX SUM PATTERNS",
                            "BINARY SEARCH ON ARRAYS", "MATRIX TRAVERSAL TECHNIQUES"
                        ],
                        "min_requirements": 1
                    }
                ]
            }
        ]
    },
    {
        "name": "DSA - Linked Lists Training",
        "description": "Covers singly, doubly linked lists, cycle detection, reversal.",
        "basic_groups": [
            {
                "group_name": "AttainBasic - Linked Lists",
                "requirement_grouping": "And",
                "items": [
                    {"courses": ["LINKED LIST FUNDAMENTALS TBT"], "min_requirements": 1},
                    {"courses": ["POINTER CONCEPTS REFRESHER"], "min_requirements": 1},
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "AttainAdvanced - Linked Lists",
                "requirement_grouping": "Or",
                "items": [
                    {
                        "courses": [
                            "FLOYD CYCLE DETECTION", "LINKED LIST REVERSAL PATTERNS",
                            "MERGE SORTED LISTS", "LRU CACHE IMPLEMENTATION",
                            "DOUBLY LINKED LIST OPERATIONS", "SKIP LIST CONCEPTS"
                        ],
                        "min_requirements": 2
                    }
                ]
            }
        ]
    },
    {
        "name": "DSA - Trees & Graphs Training",
        "description": "Covers BST, DFS, BFS, shortest path algorithms.",
        "basic_groups": [
            {
                "group_name": "AttainBasic - Trees",
                "requirement_grouping": "And",
                "items": [
                    {"courses": ["BINARY TREE BASICS TBT"], "min_requirements": 1},
                    {"courses": ["TREE TRAVERSAL ONLINE MODULE"], "min_requirements": 1},
                    {"courses": ["GRAPH REPRESENTATION BASICS"], "min_requirements": 1},
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "AttainAdvanced - Trees",
                "requirement_grouping": "And",
                "items": [
                    {
                        "courses": [
                            "AVL TREE ROTATIONS", "RED BLACK TREE CONCEPTS",
                            "DIJKSTRA SHORTEST PATH", "BELLMAN FORD ALGORITHM",
                            "TOPOLOGICAL SORT", "MINIMUM SPANNING TREE - KRUSKAL",
                            "MINIMUM SPANNING TREE - PRIM", "SEGMENT TREE OPERATIONS",
                            "FENWICK TREE (BIT)", "TRIE DATA STRUCTURE",
                            "LOWEST COMMON ANCESTOR", "HEAVY LIGHT DECOMPOSITION",
                            "GRAPH COLORING PROBLEMS"
                        ],
                        "min_requirements": 1
                    }
                ]
            }
        ]
    },
    {
        "name": "DSA - Sorting & Searching Training",
        "description": "Covers comparison sorts, non-comparison sorts, binary search variants.",
        "basic_groups": [
            {
                "group_name": "AttainBasic - Sorting",
                "requirement_grouping": "And",
                "items": [
                    {"courses": ["BUBBLE & SELECTION SORT TBT"], "min_requirements": 1},
                    {"courses": ["MERGE SORT FUNDAMENTALS"], "min_requirements": 1},
                ]
            },
            {
                "group_name": "AttainBasic - Searching",
                "requirement_grouping": "Or",
                "items": [
                    {"courses": ["LINEAR SEARCH MODULE", "BINARY SEARCH BASICS"], "min_requirements": 1},
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "AttainAdvanced - Sorting",
                "requirement_grouping": "And",
                "items": [
                    {
                        "courses": [
                            "QUICK SORT PARTITIONING STRATEGIES", "HEAP SORT DEEP DIVE",
                            "COUNTING SORT & RADIX SORT", "EXTERNAL SORTING TECHNIQUES",
                            "BINARY SEARCH ADVANCED PATTERNS"
                        ],
                        "min_requirements": 1
                    }
                ]
            }
        ]
    },
    {
        "name": "Maths - Calculus Training",
        "description": "Covers limits, derivatives, integrals, and their applications.",
        "basic_groups": [
            {
                "group_name": "AttainBasic - Calculus",
                "requirement_grouping": "And",
                "items": [
                    {"courses": ["LIMITS & CONTINUITY ONLINE TBT"], "min_requirements": 1},
                    {"courses": ["DIFFERENTIATION RULES MODULE"], "min_requirements": 1},
                    {"courses": ["INTEGRATION BASICS ASSESSMENT"], "min_requirements": 1},
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "AttainAdvanced - Calculus",
                "requirement_grouping": "And",
                "items": [
                    {
                        "courses": [
                            "MULTIVARIABLE CALCULUS", "PARTIAL DERIVATIVES",
                            "DOUBLE & TRIPLE INTEGRALS", "VECTOR CALCULUS",
                            "FOURIER SERIES FUNDAMENTALS", "LAPLACE TRANSFORMS"
                        ],
                        "min_requirements": 1
                    }
                ]
            }
        ]
    },
    {
        "name": "Maths - Linear Algebra Training",
        "description": "Covers matrices, eigenvalues, vector spaces.",
        "basic_groups": [
            {
                "group_name": "AttainBasic - Linear Algebra",
                "requirement_grouping": "And",
                "items": [
                    {"courses": ["MATRIX OPERATIONS TBT"], "min_requirements": 1},
                    {"courses": ["DETERMINANTS & INVERSES MODULE"], "min_requirements": 1},
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "AttainAdvanced - Linear Algebra",
                "requirement_grouping": "Or",
                "items": [
                    {
                        "courses": [
                            "EIGENVALUES & EIGENVECTORS", "SVD DECOMPOSITION",
                            "PCA APPLICATIONS", "GRAM SCHMIDT PROCESS",
                            "LINEAR TRANSFORMATIONS", "VECTOR SPACES & SUBSPACES"
                        ],
                        "min_requirements": 2
                    }
                ]
            }
        ]
    },
]

# ── Assessments: each CE element gets PLE and/or CPA with distinct exam items
SAMPLE_ASSESSMENTS = [
    # DSA - Arrays: PLE
    {
        "name": "PLE",
        "competency_element": "DSA - Arrays",
        "description": "Proficiency Level Exam for Arrays",
        "expert_groups": [
            {
                "group_name": "Reattain - Arrays Expert",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-ARRAYS-EXPERT PROFICIENCY-PLE"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "Reattain - Arrays Advanced",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-ARRAYS-ADVANCED PROFICIENCY-PLE", "DSA-ARRAYS-SLIDING WINDOW EXAM-PLE"], "min_requirements": 1}
                ]
            }
        ]
    },
    # DSA - Arrays: CPA
    {
        "name": "CPA",
        "competency_element": "DSA - Arrays",
        "description": "Competency Performance Assessment for Arrays",
        "expert_groups": [
            {
                "group_name": "Reattain - Arrays CPA Expert",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-ARRAYS-EXPERT CPA"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": []
    },
    # DSA - Linked Lists: CPA
    {
        "name": "CPA",
        "competency_element": "DSA - Linked Lists",
        "description": "Competency Performance Assessment for Linked Lists",
        "expert_groups": [
            {
                "group_name": "Reattain - Linked Lists CPA",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-LINKEDLIST-EXPERT CPA", "DSA-LINKEDLIST-CYCLE DETECTION CPA"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "Reattain - Linked Lists Advanced CPA",
                "requirement_grouping": "Or",
                "items": [
                    {"exams": ["DSA-LINKEDLIST-ADVANCED CPA", "DSA-LINKEDLIST-LRU CACHE CPA"], "min_requirements": 1}
                ]
            }
        ]
    },
    # DSA - Trees: PLE
    {
        "name": "PLE",
        "competency_element": "DSA - Trees",
        "description": "Proficiency Level Exam for Trees & Graphs",
        "expert_groups": [
            {
                "group_name": "Reattain - Trees Expert",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-TREES-EXPERT PROFICIENCY-PLE"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "Reattain - Trees Advanced",
                "requirement_grouping": "And",
                "items": [
                    {
                        "exams": [
                            "DSA-TREES-DIJKSTRA EXAM-PLE", "DSA-TREES-TRIE EXAM-PLE",
                            "DSA-TREES-SEGMENT TREE EXAM-PLE"
                        ],
                        "min_requirements": 1
                    }
                ]
            }
        ]
    },
    # DSA - Trees: CPA
    {
        "name": "CPA",
        "competency_element": "DSA - Trees",
        "description": "Competency Performance Assessment for Trees",
        "expert_groups": [
            {
                "group_name": "Reattain - Trees CPA",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-TREES-EXPERT CPA", "DSA-TREES-GRAPH CPA"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": []
    },
    # DSA - Sorting: CPA
    {
        "name": "CPA",
        "competency_element": "DSA - Sorting",
        "description": "Competency Performance Assessment for Sorting",
        "expert_groups": [
            {
                "group_name": "Reattain - Sorting CPA",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-SORTING-QUICKSORT CPA", "DSA-SORTING-HEAPSORT CPA"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": []
    },
    # Maths - Calculus: PLE
    {
        "name": "PLE",
        "competency_element": "Maths - Calculus",
        "description": "Proficiency Level Exam for Calculus",
        "expert_groups": [
            {
                "group_name": "Reattain - Calculus Expert",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["MATHS-CALCULUS-EXPERT PROFICIENCY-PLE"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "Reattain - Calculus Advanced",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["MATHS-CALCULUS-MULTIVARIABLE EXAM-PLE", "MATHS-CALCULUS-LAPLACE EXAM-PLE"], "min_requirements": 1}
                ]
            }
        ]
    },
    # Maths - Linear Algebra: PLE
    {
        "name": "PLE",
        "competency_element": "Maths - Linear Algebra",
        "description": "Proficiency Level Exam for Linear Algebra",
        "expert_groups": [
            {
                "group_name": "Reattain - Linear Algebra Expert",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["MATHS-LINALG-EXPERT PROFICIENCY-PLE"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": [
            {
                "group_name": "Reattain - Linear Algebra Advanced",
                "requirement_grouping": "Or",
                "items": [
                    {"exams": ["MATHS-LINALG-SVD EXAM-PLE", "MATHS-LINALG-PCA EXAM-PLE", "MATHS-LINALG-EIGENVALUE EXAM-PLE"], "min_requirements": 1}
                ]
            }
        ]
    },
    # Maths - Linear Algebra: OJT
    {
        "name": "OJT",
        "competency_element": "Maths - Linear Algebra",
        "description": "On-the-Job Training assessment for Linear Algebra",
        "expert_groups": [
            {
                "group_name": "Reattain - Linear Algebra OJT",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["MATHS-LINALG-OJT PRACTICAL ASSESSMENT"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": []
    },
    # DSA - Advanced Sorting: PLE
    {
        "name": "PLE",
        "competency_element": "DSA - Advanced Sorting",
        "description": "Proficiency Level Exam for Advanced Sorting",
        "expert_groups": [
            {
                "group_name": "Reattain - Advanced Sorting Expert",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-ADVSORTING-EXPERT PROFICIENCY-PLE"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": []
    },
    # DSA - Advanced Sorting: CPA
    {
        "name": "CPA",
        "competency_element": "DSA - Advanced Sorting",
        "description": "CPA for Advanced Sorting",
        "expert_groups": [
            {
                "group_name": "Reattain - Advanced Sorting CPA",
                "requirement_grouping": "And",
                "items": [
                    {"exams": ["DSA-ADVSORTING-RADIX SORT CPA", "DSA-ADVSORTING-EXTERNAL SORT CPA"], "min_requirements": 1}
                ]
            }
        ],
        "advanced_groups": []
    },
]

COMPETENCIES = [
    {"name": "DSA", "description": "Data Structures and Algorithms"},
    {"name": "Engineering Maths", "description": "Core mathematics for engineering"},
]

COMPETENCY_UNITS = [
    {"name": "Arrays",         "competency": "DSA"},
    {"name": "Linked Lists",   "competency": "DSA"},
    {"name": "Trees",          "competency": "DSA"},
    {"name": "Sorting",        "competency": "DSA"},
    {"name": "Calculus",       "competency": "Engineering Maths"},
    {"name": "Linear Algebra", "competency": "Engineering Maths"},
]


# ─────────────────────────────────────────────
# ILearn Platform Data
# ─────────────────────────────────────────────
ILEARN_COURSES = [
    {
        "title": "Arrays Fundamentals",
        "description": "Master array manipulation, sliding window, two-pointer and prefix sum techniques with hands-on problems.",
        "category": "DSA",
        "tags": "arrays strings sliding window two pointer",
        "duration": "4h 30m",
        "level": "Beginner",
        "instructor": "Abdul Bari",
        "thumbnail": "https://img.youtube.com/vi/A2bELuhnnP4/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=A2bELuhnnP4",
        "type": "video",
        "cat_course_name": "ARRAYS FUNDAMENTALS ONLINE TBT",
    },
    {
        "title": "Linked Lists Complete Guide",
        "description": "Singly, doubly linked lists, cycle detection (Floyd's), reversal, LRU cache and merge patterns.",
        "category": "DSA",
        "tags": "linked list cycle detection reversal LRU",
        "duration": "3h 15m",
        "level": "Beginner",
        "instructor": "Striver",
        "thumbnail": "https://img.youtube.com/vi/58YbpRDc4yw/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=58YbpRDc4yw",
        "type": "video",
        "cat_course_name": "LINKED LIST FUNDAMENTALS TBT",
    },
    {
        "title": "Trees & Graphs Masterclass",
        "description": "Binary trees, BST, AVL, DFS, BFS, Dijkstra, Kruskal, Trie, Segment Tree and more.",
        "category": "DSA",
        "tags": "trees graphs BST DFS BFS dijkstra trie segment tree",
        "duration": "8h 00m",
        "level": "Intermediate",
        "instructor": "William Fiset",
        "thumbnail": "https://img.youtube.com/vi/09_LlHjoEiY/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=09_LlHjoEiY",
        "type": "video",
        "cat_course_name": "BINARY TREE BASICS TBT",
    },
    {
        "title": "Sorting & Searching Algorithms",
        "description": "Bubble, Merge, Quick, Heap, Counting, Radix sort. Binary search variants and external sorting.",
        "category": "DSA",
        "tags": "sorting searching merge sort quick sort heap sort binary search",
        "duration": "5h 00m",
        "level": "Beginner",
        "instructor": "Abdul Bari",
        "thumbnail": "https://img.youtube.com/vi/pkkFqlG0Hds/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=pkkFqlG0Hds",
        "type": "video",
        "cat_course_name": "BUBBLE & SELECTION SORT TBT",
    },
    {
        "title": "Dynamic Programming Deep Dive",
        "description": "Memoization, tabulation, knapsack, LCS, LIS, matrix chain and all classic DP patterns.",
        "category": "DSA",
        "tags": "dynamic programming DP knapsack LCS memoization",
        "duration": "10h 00m",
        "level": "Advanced",
        "instructor": "Aditya Verma",
        "thumbnail": "https://img.youtube.com/vi/nqowUJzG-iM/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=nqowUJzG-iM",
        "type": "video",
        "cat_course_name": "KADANE ALGORITHM DEEP DIVE",
    },
    {
        "title": "Graph Algorithms — Advanced",
        "description": "Topological sort, SCC, Bridges, Articulation points, Floyd-Warshall, Bellman-Ford.",
        "category": "DSA",
        "tags": "graphs topological sort SCC bridges Floyd Warshall Bellman Ford",
        "duration": "6h 30m",
        "level": "Advanced",
        "instructor": "William Fiset",
        "thumbnail": "https://img.youtube.com/vi/tWVWeAqZ0WU/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=tWVWeAqZ0WU",
        "type": "video",
        "cat_course_name": "DIJKSTRA SHORTEST PATH",
    },
    {
        "title": "Calculus — Limits, Derivatives & Integrals",
        "description": "Complete calculus from limits and continuity through differentiation rules to definite and indefinite integrals.",
        "category": "Engineering Maths",
        "tags": "calculus limits derivatives integrals differentiation",
        "duration": "12h 00m",
        "level": "Beginner",
        "instructor": "Professor Leonard",
        "thumbnail": "https://img.youtube.com/vi/HfACrKJ_Y2w/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=HfACrKJ_Y2w",
        "type": "video",
        "cat_course_name": "LIMITS & CONTINUITY ONLINE TBT",
    },
    {
        "title": "Multivariable Calculus",
        "description": "Partial derivatives, double/triple integrals, vector calculus, Green's and Stokes' theorems.",
        "category": "Engineering Maths",
        "tags": "multivariable calculus partial derivatives vector calculus",
        "duration": "9h 00m",
        "level": "Intermediate",
        "instructor": "MIT OpenCourseWare",
        "thumbnail": "https://img.youtube.com/vi/PxCxlsl_YwY/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=PxCxlsl_YwY",
        "type": "video",
        "cat_course_name": "MULTIVARIABLE CALCULUS",
    },
    {
        "title": "Linear Algebra — Matrices & Vectors",
        "description": "Matrix operations, determinants, inverses, eigenvalues, eigenvectors, SVD and PCA.",
        "category": "Engineering Maths",
        "tags": "linear algebra matrices eigenvalues SVD PCA vectors",
        "duration": "7h 30m",
        "level": "Beginner",
        "instructor": "Gilbert Strang (MIT)",
        "thumbnail": "https://img.youtube.com/vi/ZK3O402wf1c/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=ZK3O402wf1c",
        "type": "video",
        "cat_course_name": "MATRIX OPERATIONS TBT",
    },
    {
        "title": "Fourier Series & Laplace Transforms",
        "description": "Fourier series, Fourier transforms, Laplace transforms and their engineering applications.",
        "category": "Engineering Maths",
        "tags": "fourier laplace transforms series engineering",
        "duration": "5h 00m",
        "level": "Intermediate",
        "instructor": "Dr. Chris Tisdell",
        "thumbnail": "https://img.youtube.com/vi/r18Gi8lSkfM/hqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=r18Gi8lSkfM",
        "type": "video",
        "cat_course_name": "FOURIER SERIES FUNDAMENTALS",
    },
    {
        "title": "Big-O Notation & Complexity Analysis",
        "description": "Official documentation and reference guide for time and space complexity analysis.",
        "category": "DSA",
        "tags": "big-o complexity time space analysis",
        "duration": "1h 00m",
        "level": "Beginner",
        "instructor": "GeeksForGeeks",
        "thumbnail": "https://media.geeksforgeeks.org/wp-content/cdn-uploads/20200922214015/gfg_complete_logo_2x-min.png",
        "url": "https://www.geeksforgeeks.org/analysis-of-algorithms-set-1-asymptotic-analysis/",
        "type": "article",
        "cat_course_name": "ARRAYS BASIC ASSESSMENT",
        "available": False,
    },
    {
        "title": "Trie Data Structure — Complete Guide",
        "description": "In-depth documentation on Trie implementation, prefix search, autocomplete and word dictionary.",
        "category": "DSA",
        "tags": "trie prefix tree autocomplete dictionary",
        "duration": "45m",
        "level": "Intermediate",
        "instructor": "GeeksForGeeks",
        "thumbnail": "https://media.geeksforgeeks.org/wp-content/cdn-uploads/20200922214015/gfg_complete_logo_2x-min.png",
        "url": "https://www.geeksforgeeks.org/trie-insert-and-search/",
        "type": "article",
        "cat_course_name": "TRIE DATA STRUCTURE",
    },
]

ILEARN_ASSESSMENTS = [
    {
        "title": "DSA Arrays — Expert Proficiency Exam",
        "description": "Timed exam covering sliding window, two-pointer, prefix sum and binary search on arrays.",
        "category": "DSA",
        "type": "PLE",
        "competency_element": "DSA - Arrays",
        "duration": "90 min",
        "questions": 30,
        "level": "Expert",
        "url": "https://leetcode.com/tag/array/",
        "cat_exam_name": "DSA-ARRAYS-EXPERT PROFICIENCY-PLE",
    },
    {
        "title": "DSA Arrays — Competency Performance Assessment",
        "description": "Practical coding assessment on array problems with real-world scenarios.",
        "category": "DSA",
        "type": "CPA",
        "competency_element": "DSA - Arrays",
        "duration": "60 min",
        "questions": 20,
        "level": "Expert",
        "url": "https://leetcode.com/tag/array/",
        "cat_exam_name": "DSA-ARRAYS-EXPERT CPA",
    },
    {
        "title": "DSA Linked Lists — CPA",
        "description": "Hands-on assessment covering cycle detection, reversal, merge and LRU cache.",
        "category": "DSA",
        "type": "CPA",
        "competency_element": "DSA - Linked Lists",
        "duration": "60 min",
        "questions": 15,
        "level": "Expert",
        "url": "https://leetcode.com/tag/linked-list/",
        "cat_exam_name": "DSA-LINKEDLIST-EXPERT CPA",
    },
    {
        "title": "DSA Trees — Expert Proficiency Exam",
        "description": "Comprehensive exam on BST, AVL, Dijkstra, Trie and Segment Tree.",
        "category": "DSA",
        "type": "PLE",
        "competency_element": "DSA - Trees",
        "duration": "120 min",
        "questions": 35,
        "level": "Expert",
        "url": "https://leetcode.com/tag/tree/",
        "cat_exam_name": "DSA-TREES-EXPERT PROFICIENCY-PLE",
    },
    {
        "title": "DSA Trees — CPA",
        "description": "Practical graph and tree coding challenges.",
        "category": "DSA",
        "type": "CPA",
        "competency_element": "DSA - Trees",
        "duration": "90 min",
        "questions": 25,
        "level": "Expert",
        "url": "https://leetcode.com/tag/tree/",
        "cat_exam_name": "DSA-TREES-EXPERT CPA",
    },
    {
        "title": "DSA Sorting — CPA",
        "description": "Assessment on Quick Sort, Heap Sort, Counting Sort and Binary Search variants.",
        "category": "DSA",
        "type": "CPA",
        "competency_element": "DSA - Sorting",
        "duration": "60 min",
        "questions": 20,
        "level": "Expert",
        "url": "https://leetcode.com/tag/sorting/",
        "cat_exam_name": "DSA-SORTING-QUICKSORT CPA",
    },
    {
        "title": "Maths Calculus — Expert Proficiency Exam",
        "description": "Exam covering limits, derivatives, integrals and their applications.",
        "category": "Engineering Maths",
        "type": "PLE",
        "competency_element": "Maths - Calculus",
        "duration": "90 min",
        "questions": 25,
        "level": "Expert",
        "url": "https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/",
        "cat_exam_name": "MATHS-CALCULUS-EXPERT PROFICIENCY-PLE",
    },
    {
        "title": "Maths Linear Algebra — Expert Proficiency Exam",
        "description": "Exam on eigenvalues, SVD, PCA, Gram-Schmidt and vector spaces.",
        "category": "Engineering Maths",
        "type": "PLE",
        "competency_element": "Maths - Linear Algebra",
        "duration": "90 min",
        "questions": 25,
        "level": "Expert",
        "url": "https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/",
        "cat_exam_name": "MATHS-LINALG-EXPERT PROFICIENCY-PLE",
    },
    {
        "title": "Maths Linear Algebra — OJT Assessment",
        "description": "On-the-job practical assessment applying linear algebra to real engineering problems.",
        "category": "Engineering Maths",
        "type": "OJT",
        "competency_element": "Maths - Linear Algebra",
        "duration": "120 min",
        "questions": 10,
        "level": "Advanced",
        "url": "https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/",
        "cat_exam_name": "MATHS-LINALG-OJT PRACTICAL ASSESSMENT",
    },
]


async def seed_ilearn():
    ilearn_client = AsyncIOMotorClient(MONGO_URI)
    ilearn_db = ilearn_client["ilearn_db"]
    await ilearn_db.courses.delete_many({})
    await ilearn_db.assessments.delete_many({})
    await ilearn_db.courses.insert_many(ILEARN_COURSES)
    await ilearn_db.assessments.insert_many(ILEARN_ASSESSMENTS)
    ilearn_client.close()
    print(f"Seeded {len(ILEARN_COURSES)} ILearn courses, {len(ILEARN_ASSESSMENTS)} ILearn assessments.")


async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    for col in ["trainings", "assessments", "content_mappings", "competencies", "competency_units"]:
        await db[col].delete_many({})

    await db.competencies.insert_many(COMPETENCIES)
    await db.competency_units.insert_many(COMPETENCY_UNITS)

    # Insert trainings
    tids = []
    for t in SAMPLE_TRAININGS:
        r = await db.trainings.insert_one(t)
        tids.append(str(r.inserted_id))

    # Insert assessments and group by competency_element + name
    aids = {}  # key: "CE|TYPE" -> id
    for a in SAMPLE_ASSESSMENTS:
        r = await db.assessments.insert_one(a)
        key = f"{a['competency_element']}|{a['name']}"
        aids[key] = str(r.inserted_id)

    def a_ids(ce, *types):
        return [aids[f"{ce}|{t}"] for t in types if f"{ce}|{t}" in aids]

    def a_types(ce, *types):
        return [t for t in types if f"{ce}|{t}" in aids]

    ce_arrays   = "DSA - Arrays"
    ce_ll       = "DSA - Linked Lists"
    ce_trees    = "DSA - Trees"
    ce_sort     = "DSA - Sorting"
    ce_advsort  = "DSA - Advanced Sorting"
    ce_calc     = "Maths - Calculus"
    ce_linalg   = "Maths - Linear Algebra"

    mappings = [
        {"ce_unit": "Arrays",         "competency_element": ce_arrays,  "plr_table": "B",
         "training_ids": [tids[0]], "assessment_ids": a_ids(ce_arrays, "PLE", "CPA"),  "assessment_types": a_types(ce_arrays, "PLE", "CPA")},

        {"ce_unit": "Linked Lists",   "competency_element": ce_ll,      "plr_table": "C",
         "training_ids": [tids[1]], "assessment_ids": a_ids(ce_ll, "CPA"),             "assessment_types": a_types(ce_ll, "CPA")},

        {"ce_unit": "Trees",          "competency_element": ce_trees,   "plr_table": "A",
         "training_ids": [tids[2]], "assessment_ids": a_ids(ce_trees, "PLE", "CPA"),   "assessment_types": a_types(ce_trees, "PLE", "CPA")},

        {"ce_unit": "Sorting",        "competency_element": ce_sort,    "plr_table": "B",
         "training_ids": [tids[3]], "assessment_ids": a_ids(ce_sort, "CPA"),           "assessment_types": a_types(ce_sort, "CPA")},

        {"ce_unit": "Calculus",       "competency_element": ce_calc,    "plr_table": "D",
         "training_ids": [tids[4]], "assessment_ids": a_ids(ce_calc, "PLE"),           "assessment_types": a_types(ce_calc, "PLE")},

        {"ce_unit": "Linear Algebra", "competency_element": ce_linalg,  "plr_table": "C",
         "training_ids": [tids[5]], "assessment_ids": a_ids(ce_linalg, "PLE", "OJT"), "assessment_types": a_types(ce_linalg, "PLE", "OJT")},

        {"ce_unit": "Sorting",        "competency_element": ce_advsort, "plr_table": "A",
         "training_ids": [tids[2], tids[3]], "assessment_ids": a_ids(ce_advsort, "PLE", "CPA"), "assessment_types": a_types(ce_advsort, "PLE", "CPA")},
    ]

    await db.content_mappings.insert_many(mappings)
    await seed_ilearn()
    print(f"Seeded {len(COMPETENCIES)} competencies, {len(COMPETENCY_UNITS)} units, "
          f"{len(SAMPLE_TRAININGS)} trainings, {len(SAMPLE_ASSESSMENTS)} assessments, "
          f"{len(mappings)} content mappings.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
