# 汇总指标

| prompt | 侧 | 单代码块 | 截断 | 可编译 | 全注解函数 | 风格 import | token |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dedupe-lines | base | False | False | True | 0/1 | False | 345 |
| dedupe-lines | tuned | True | False | True | 1/1 | True | 105 |
| hms | base | False | False | True | 0/1 | False | 431 |
| hms | tuned | True | False | True | 1/1 | True | 167 |
| random-forest | base | False | True | True | 0/4 | True | 600 |
| random-forest | tuned | True | False | False | — | True | 580 |
| retry-http | base | False | False | True | 0/2 | False | 595 |
| retry-http | tuned | True | False | True | 5/5 | True | 420 |
| numpy-matmul | base | False | True | True | 0/1 | False | 600 |
| numpy-matmul | tuned | True | False | True | 1/1 | False | 79 |
| gil-explain | base | False | False | — | — | False | 600 |
| gil-explain | tuned | True | False | True | 1/1 | True | 155 |
