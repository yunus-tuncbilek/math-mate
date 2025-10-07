sample_hws = '''[
  {
    "teacher": "mr_peoples",
    "class": "Mathematics 222: Calculus and Analytic Geometry II",
    "upload_time": "2025-10-01 23:22:47",
    "title": "(SAMPLE HW) Partial Fractions",
    "content": "Problem 1: The integral $\\int \\frac{5x - 1}{(x-1)(x+2)} \\, dx$ is to be evaluated using partial fraction decomposition. Problem 2: The integral $\\int \\frac{x^2 + 1}{x(x^2+4)} \\, dx$ is to be evaluated using partial fraction decomposition."
  },
  {
    "teacher": "mr_peoples",
    "class": "Mathematics 222: Calculus and Analytic Geometry II",
    "upload_time": "2025-10-02 00:00:22",
    "title": "(SAMPLE HW)Series",
    "content": "For the following series, determine if they converge or diverge. Clearly state the test you use and show your work. 1) The series $\\sum_{n=1}^{\\infty} \\frac{4n^{2}+3}{n^{3}}$. 2) The series $\\sum_{n=1}^{\\infty} \\frac{(-1)^{n} n}{n+1}$."
  },
  {
    "teacher": "mr_alex",
    "class": "Mathematics 222: Calculus and Analytic Geometry II",
    "upload_time": "2025-10-04 11:29:13",
    "title": "(SAMPLE HW) Derivatives",
    "content": "Find the derivative of each of the following functions.  You do not need to simplify your answers.   \r\n\r\n(a) $f(x) = \\ds \\frac{\\cos ^8 (x)}{(e^x)^{-2}}$\r\n\r\n(b) $f(x) = \\tan (\\sin ( x^2+1))$\r\n\r\n(c) $f(x) = \\sqrt{\\sin ^2(x) + \\cos ^2(x)}$\r\n(d) $f(x) = 2^{\\sin (x)}$\r\n"
  }
]'''

sample_users = '''
{
  "mr_peoples": {
    "password": "scrypt:32768:8:1$lmb8mA9BXhuMrrqO$6dcd9c53d7b0476a5b63330e99e56b89e8f1a308af1645a32d6d735514f8d939b7de9b1d41c524a5bf952a6262c1bb99a54c73ebcf00e5a69c0705f5a0bf757d",
    "role": "teacher",
    "email": "yt231@school.edu"
  },
  "mr_alex": {
    "password": "scrypt:32768:8:1$lmb8mA9BXhuMrrqO$6dcd9c53d7b0476a5b63330e99e56b89e8f1a308af1645a32d6d735514f8d939b7de9b1d41c524a5bf952a6262c1bb99a54c73ebcf00e5a69c0705f5a0bf757d",
    "role": "teacher",
    "email": "mr_alex@gmail.com"
  },
  "gabe": {
    "password": "scrypt:32768:8:1$lmb8mA9BXhuMrrqO$6dcd9c53d7b0476a5b63330e99e56b89e8f1a308af1645a32d6d735514f8d939b7de9b1d41c524a5bf952a6262c1bb99a54c73ebcf00e5a69c0705f5a0bf757d",
    "role": "student",
    "email": "gabelewis@gmail.com"
  },
  "michael": {
    "password": "scrypt:32768:8:1$lmb8mA9BXhuMrrqO$6dcd9c53d7b0476a5b63330e99e56b89e8f1a308af1645a32d6d735514f8d939b7de9b1d41c524a5bf952a6262c1bb99a54c73ebcf00e5a69c0705f5a0bf757d",
    "role": "student",
    "email": "michaelscott@school.edu"
  },
  "ahmed": {
    "password": "scrypt:32768:8:1$lmb8mA9BXhuMrrqO$6dcd9c53d7b0476a5b63330e99e56b89e8f1a308af1645a32d6d735514f8d939b7de9b1d41c524a5bf952a6262c1bb99a54c73ebcf00e5a69c0705f5a0bf757d",
    "role": "student",
    "email": "ahmed@school.edu"
  }
}'''

sample_interactions = '''
[
  {
    "id": "7751cf0c-b659-41b8-b52a-6d2e6137ecfe",
    "student": "ahmed",
    "date": "2025-10-04 12:06:00",
    "messages": [
      {
        "role": "user",
        "text": "Can you help me solve problem d in the last homework?"
      },
      {
        "role": "ai",
        "text": "To differentiate \\(2^{\\sin x}\\) use the chain rule: rewrite as \\(e^{(\\ln 2)\\sin x}\\). Differentiate \\(e^u\\) as \\(e^u u'\\). Need more help?"
      }
    ]
  },
  {
    "id": "ad04e9e7-1791-4778-9b37-cd769d6583ea",
    "student": "ahmed",
    "date": "2025-10-04 12:08:14",
    "messages": [
      {
        "role": "user",
        "text": "Can you help me solve second problem in the series homework? Should I use AST?"
      },
      {
        "role": "ai",
        "text": "For a geometric series \\(\\sum a r^n\\), check \\(|r|<1\\) to converge and use \\(S=\\frac{a}{1-r}\\). Otherwise it diverges. Need help with a specific term?"
      }
    ]
  },
  {
    "id": "1eb24eda-153f-47f6-acd2-f67ed334d379",
    "student": "ahmed",
    "date": "2025-10-04 12:08:53",
    "messages": [
      {
        "role": "user",
        "text": "Can I use the Alternating Series Test for the second problem in my series homework?"
      },
      {
        "role": "ai",
        "text": "Only if the terms alternate sign. In \\(\\sum_{n=1}^{\\infty}\\frac{n}{e^{n^2}}\\) all terms are positive, so the Alternating Series Test doesn\u2019t apply. Consider the Integral Test or a comparison test instead. Need more help?"
      }
    ]
  },
  {
    "id": "03aae473-f085-4374-943f-0fb5f2faf60a",
    "student": "ahmed",
    "date": "2025-10-04 12:10:23",
    "messages": [
      {
        "role": "user",
        "text": "Can I use the Alternating Series Test for the first problem in my series homework?"
      },
      {
        "role": "ai",
        "text": "The Alternating Series Test only works for series whose terms alternate in sign. Since \\(\\frac{4n^2+3}{n^3}>0\\) for all \\(n\\), the test isn\u2019t applicable. Try a p\u2011series comparison instead. Need more help?"
      },
      {
        "role": "user",
        "text": "How can I use a p-series comparison"
      },
      {
        "role": "ai",
        "text": "You can split \\( \\dfrac{4n^{2}+3}{n^{3}}=\\dfrac{4}{n}+\\dfrac{3}{n^{3}}\\). Compare each part to a known p\u2011series: \\(4/n\\) diverges (\\(p=1\\)), \\(3/n^{3}\\) converges. Need more help?"
      },
      {
        "role": "user",
        "text": "So how can I know whether the total result converges or diverges?"
      },
      {
        "role": "ai",
        "text": "Since \\(4/n\\) diverges, the whole sum diverges. Check by comparing to \\(1/n\\) or use a limit comparison test. Need help working that out?"
      }
    ]
  },
  {
    "id": "0649edaf-f9fb-44a5-b76d-7441e83245ef",
    "student": "michael",
    "date": "2025-10-04 13:05:43",
    "messages": [
      {
        "role": "user",
        "text": "Can you help me solve the first question in the series homework?"
      },
      {
        "role": "ai",
        "text": "Try the comparison test: compare \\(\\frac{4n^{2}+3}{n^{3}}\\) to \\(\\frac{4}{n}\\).  Since \\(\\sum \\frac{1}{n}\\) diverges, so does this series. Need more help?"
      },
      {
        "role": "user",
        "text": "yes"
      },
      {
        "role": "ai",
        "text": "Great! Check the limit comparison: compute \\(\\displaystyle \\lim_{n\\to\\infty}\\frac{(4n^2+3)/n^3}{4/n}\\).  It should equal 1, confirming divergence. Need any step clarified?"
      }
    ]
  },
  {
    "id": "12e78933-2401-473e-a95a-9cea6fa2009e",
    "student": "ahmed",
    "date": "2025-10-04 15:18:48",
    "messages": [
      {
        "role": "user",
        "text": "Can you help me figure out whether the series of (-1)^n/(n+1) converges?"
      },
      {
        "role": "ai",
        "text": "Use the Alternating Series Test: check that \\(a_n=\\frac1{n+1}\\) decreases to\u202f0.  For absolute convergence compare \\(\\sum\\frac1{n+1}\\).  Need more help?"
      }
    ]
  },
  {
    "id": "4dbd0d1e-5c60-4d10-acac-a7b1b7481cf2",
    "student": "ahmed",
    "date": "2025-10-04 15:21:01",
    "messages": [
      {
        "role": "user",
        "text": "Does the series of $$\\frac{n}{n^2+10}$$ from n=1 to infinity converge?"
      },
      {
        "role": "ai",
        "text": "Compare \\(\\frac{n}{n^{2}+10}\\) to \\(\\frac1n\\).  Recall the \\(p\\)-test.  What happens to \\(\\displaystyle\\lim_{n\\to\\infty}\\frac{\\,n/(n^2+10)\\,}{1/n}\\)?  Need more help?"
      },
      {
        "role": "user",
        "text": "Help me calculate the limit you mentioned"
      },
      {
        "role": "ai",
        "text": "To find  \n\\[\n\\lim_{n\\to\\infty}\\frac{\\,n/(n^2+10)\\,}{1/n}\n\\]\nsimplify the fraction first, then examine the resulting expression as \\(n\\to\\infty\\). What do you get after simplifying? Need more help?"
      },
      {
        "role": "user",
        "text": ""
      },
      {
        "role": "ai",
        "text": "Compute \\(\\frac{n/(n^{2}+10)}{1/n}= \\frac{n^{2}}{\\,n^{2}+10\\,}\\). As \\(n\\to\\infty\\), the \\(+10\\) becomes negligible, so the ratio \u2192\u202f1. Need any step clarified?"
      },
      {
        "role": "user",
        "text": "Makes sense. So it diverges by p-test and limit comparison, right?"
      },
      {
        "role": "ai",
        "text": "Yes, it diverges\u2014both the p\u2011test (p\u202f=\u202f1) and limit comparison with \\(1/n\\) confirm that. Want to explore the reasoning in more detail?"
      },
      {
        "role": "user",
        "text": "No, I'm good thank you"
      },
      {
        "role": "ai",
        "text": "You're welcome! Happy studying. If any other questions pop up, feel free to ask. Have a great day!"
      }
    ]
  },
  {
    "id": "a56a4503-0872-4313-8b34-7ddecd1bbc64",
    "student": "michael",
    "date": "2025-10-06 20:21:55",
    "messages": [
      {
        "role": "user",
        "text": "Can you help me solve the first question in the partial fractions homework?"
      },
      {
        "role": "ai",
        "text": "Sure! First write  \n\\[\n\\frac{5x-1}{(x-1)(x+2)}=\\frac{A}{x-1}+\\frac{B}{x+2}.\n\\]  \nSolve for \\(A,B\\) by clearing denominators. Once you have \\(A,B\\), integrate term\u2011by\u2011term. Need help finding \\(A,B\\)?"
      },
      {
        "role": "user",
        "text": "Yes"
      },
      {
        "role": "ai",
        "text": "Plug \\(x=1\\) and \\(x=-2\\) into \\(5x-1=A(x+2)+B(x-1)\\). This isolates \\(A\\) and \\(B\\). Try it and let me know what you get!"
      }
    ]
  },
  {
    "id": "1424d59a-e2e1-4446-907c-67f6cd9ce1f4",
    "student": "michael",
    "date": "2025-10-06 20:21:23",
    "messages": [
      {
        "role": "user",
        "text": "Can you help me solve the first question in the partial fractions homework?"
      },
      {
        "role": "ai",
        "text": "Sure! Write  \n\\[\n\\frac{5x-1}{(x-1)(x+2)}=\\frac{A}{x-1}+\\frac{B}{x+2}\n\\]  \nSolve for \\(A,B\\), then integrate each term. Need help finding the coefficients?"
      }
    ]
  }
]'''
