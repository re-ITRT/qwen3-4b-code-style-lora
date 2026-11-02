# 风格对比：基座 Qwen3-4B vs LoRA 微调

- 基座：`Qwen/Qwen3-4B`（未挂 adapter）
- 微调：`Qwen/Qwen3-4B` + LoRA `./sft-minimal-output`
- 解码：greedy（`do_sample=False`），两侧完全相同的 prompt 与 token 上限

---

## dedupe-lines（in-domain）

> 我想要一个去掉文本空行和首尾空白的函数，参数接受任意可迭代的字符串，返回 list，空输入返回空列表。

| | 指标 |
| --- | --- |
| 基座 | 单代码块=False | 可编译=True | 全注解函数=0/1 | 风格 import=False | 散文 300 字符 | 345 token |
| 微调 | 单代码块=True | 可编译=True | 全注解函数=1/1 | 风格 import=True | 散文 0 字符 | 105 token |

### 基座输出

````text
你可以使用 Python 编写一个函数，该函数接收任意可迭代的字符串（如列表、元组、生成器等），去除其中的空行和首尾空白，然后返回一个列表。

下面是一个实现该功能的函数：

```python
def remove_empty_lines_and_trailing_whitespace(iterable):
    """
    去除输入可迭代对象中的空行和首尾空白，返回一个列表。
    
    参数:
        iterable: 任意可迭代的字符串（如列表、元组、生成器等）
        
    返回:
        list: 去除空行和首尾空白后的字符串列表
    """
    result = []
    for item in iterable:
        stripped = item.strip()
        if stripped:
            result.append(stripped)
    return result
```

### 示例用法：

```python
input_data = [
    "  Hello World  ",
    "",
    "  Python  ",
    "   ",
    "  Test  ",
    ""
]

output = remove_empty_lines_and_trailing_whitespace(input_data)
print(output)
```

### 输出结果：

```
['Hello World', 'Python', 'Test']
```

### 说明：

- `item.strip()` 会去除字符串的首尾空白（包括空格、制表符、换行符等）。
- 如果 `stripped` 不为空字符串，则将其添加到结果列表中。
- 空输入（如空列表）会返回空列表。

如果你希望处理的是每一行的字符串（比如从文件中读取的行），也可以使用 `str.strip()` 来处理每一行。这个函数适用于大多数字符串迭代场景。
````


### 微调输出

````text
```python
from collections.abc import Iterable


def collapse_lines(lines: Iterable[str]) -> list[str]:
    """去掉空行、首尾空白，保持中间非空行的顺序。"""
    out: list[str] = []
    for line in lines:
        text = line.strip()
        if text and text not in out:
            out.append(text)
    return out


if __name__ == '__main__':
    print(collapse_lines([' a b', '', 'c', ' a b']))
```
````


---

## hms（in-domain）

> 帮我写一个把秒数转成时分秒字符串的函数，秒数接受任意实数并向下取整，负数返回 00:00:00。

| | 指标 |
| --- | --- |
| 基座 | 单代码块=False | 可编译=True | 全注解函数=0/1 | 风格 import=False | 散文 246 字符 | 431 token |
| 微调 | 单代码块=True | 可编译=True | 全注解函数=1/1 | 风格 import=True | 散文 0 字符 | 167 token |

### 基座输出

````text
当然可以！下面是一个将秒数转换为 `HH:MM:SS` 格式字符串的函数。这个函数会：

- 接受任意实数（如 `123.45`）作为输入。
- 先对秒数进行 **向下取整**（即 `floor`）。
- 如果秒数为负数，返回 `00:00:00`。
- 否则，将秒数转换为小时、分钟和秒，并格式化为 `HH:MM:SS`。

下面是 Python 实现：

```python
def seconds_to_hms(seconds):
    # 如果输入为负数，返回 00:00:00
    if seconds < 0:
        return "00:00:00"
    
    # 向下取整
    total_seconds = int(seconds)
    
    # 计算小时、分钟、秒
    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    
    # 格式化为 HH:MM:SS
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
```

### 示例：

```python
print(seconds_to_hms(3661))     # 输出: 01:01:01
print(seconds_to_hms(123.45))   # 输出: 00:02:03
print(seconds_to_hms(-5))       # 输出: 00:00:00
print(seconds_to_hms(0))        # 输出: 00:00:00
print(seconds_to_hms(3600))     # 输出: 01:00:00
```

如果你需要其他语言的版本（如 JavaScript、Java 等），也可以告诉我，我可以为你提供相应版本。
````


### 微调输出

````text
```python
from numbers import Real


def seconds_to_hms(total: Real) -> str:
    """把秒数转成 00:00:00 形式，负数返回 00:00:00。"""
    seconds = int(total)
    if seconds <= 0:
        return '00:00:00'
    hours = seconds // 3600
    remainder = seconds % 3600
    minutes = remainder // 60
    return f'{hours:02d}:{minutes:02d}:{seconds % 60:02d}'


if __name__ == '__main__':
    print(seconds_to_hms(3661))
    print(seconds_to_hms(-5))
```
````


---

## random-forest（held-out）

> 写一个 sklearn 兼容的随机森林类

| | 指标 |
| --- | --- |
| 基座 | 单代码块=False | 可编译=True | 全注解函数=0/4 | 风格 import=True | 散文 420 字符 | 600 token | **截断** |
| 微调 | 单代码块=True | 可编译=False | 全注解函数=— | 风格 import=True | 散文 0 字符 | 580 token |

### 基座输出

````text
当然可以！下面是一个 **sklearn 兼容的随机森林类**，它继承自 `BaseEstimator` 和 `ClassifierMixin`（如果是分类任务），并实现了 `fit` 和 `predict` 方法。这个类使用了 `scikit-learn` 的 `RandomForestClassifier` 或 `RandomForestRegressor` 的内部逻辑，但用 Python 实现，以便你理解其内部机制。

---

## ✅ 说明

- 该类是 **sklearn 兼容的**，即它实现了 `fit`、`predict`、`score` 等方法。
- 它使用了 **随机森林的基分类器（如决策树）**。
- 该类是 **简化版**，仅用于学习和理解，不适用于生产环境。

---

## 🧩 代码实现

```python
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.utils import resample

class RandomForestClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, n_estimators=100, max_depth=None, min_samples_split=2):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.trees = []

    def fit(self, X, y):
        # 检查输入
        X, y = check_X_y(X, y)
        n_samples, n_features = X.shape

        # 训练每棵树
        for _ in range(self.n_estimators):
            # 随机采样
            indices = np.random.choice(n_samples, n_samples, replace=True)
            X_sample = X[indices]
            y_sample = y[indices]

            # 随机选择特征
            features = np.random.choice(n_features, n_features, replace=True)

            # 创建决策树
            tree = DecisionTreeClassifier(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=42
            )
            tree.fit(X_sample[:, features], y_sample)

            self.trees.append(tree)

        return self

    def predict(self, X):
        check_is_fitted(self, "trees")
        X = check_array(X)
        y_pred = np.zeros(X.shape[0])

        for tree in self.trees:
            y_pred += tree.predict(X)

        return np.round(y_pred / len(self.trees))

    def score(self, X, y):
        check_is_fitted(self, "trees")
        X, y = check_X_y(X, y)
        y_pred = self.predict(X)
        return np.mean(y_pred == y)
```

---

## 🧪 示例用法

```python
from sklearn.datasets import
````


### 微调输出

````text
```python
import numpy as np
from numbers import Real
from typing import Sequence, Union
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.utils.validation import check_array, check_is_fitted


class SklearnRF:
    """sklearn 兼容的随机森林类，支持分类和回归。"""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Union[int, Real] = None,
        min_samples_split: Union[int, Real] = 2,
        random_state: Union[int, Real] = None,
    ) -> None:
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        self.estimators: list[DecisionTreeClassifier] = []
        self.classes_ = None

    def fit(
        self, X: Sequence[Sequence[Real]], y: Sequence[Real]
    ) -> 'SklearnRF':
        """训练模型。"""
        X = check_array(X)
        y = np.array(y, dtype=int)
        self.estimators = []
        for _ in range(self.n_estimators):
            tree = DecisionTreeClassifier(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=self.random_state,
            )
            tree.fit(X, y)
            self.estimators.append(tree)
        self.classes_ = np.unique(y)
        return self

    def predict(
        self, X: Sequence[Sequence[Real]] -> Sequence[int]
    ) -> np.ndarray:
        """预测类别。"""
        X = check_array(X)
        check_is_fitted(self, ['classes_'])
        preds = np.array([tree.predict(X) for tree in self.estimators])
        return np.apply_along_axis(lambda row: np.bincount(row).argmax(), axis=0, arr=preds)

    def predict_proba(
        self, X: Sequence[Sequence[Real]] -> np.ndarray
    ) -> np.ndarray:
        """预测概率。"""
        X = check_array(X)
        check_is_fitted(self, ['classes_'])
        preds = np.array([tree.predict_proba(X) for tree in self.estimators])
        counts = np.apply_along_axis(lambda row: np.sum(row, axis=0), axis=0, arr=preds)
        return np.apply_along_axis(lambda row: row / counts, axis=1, arr=preds)


if __name__ == '__main__':
    rf = SklearnRF(n_estimators=1)
    rf.fit([[0.0], [1.0]], [0, 1])
    print(rf.predict([[0.5]]))
```
````


---

## retry-http（held-out）

> 帮我写一个带重试的 HTTP 请求函数，最多重试 3 次，失败时抛异常。

| | 指标 |
| --- | --- |
| 基座 | 单代码块=False | 可编译=True | 全注解函数=0/2 | 风格 import=False | 散文 587 字符 | 595 token |
| 微调 | 单代码块=True | 可编译=True | 全注解函数=5/5 | 风格 import=True | 散文 0 字符 | 420 token |

### 基座输出

````text
当然可以！下面是一个使用 Python 编写的带重试机制的 HTTP 请求函数，最多重试 3 次，如果所有尝试都失败，则抛出异常。

这个函数使用了 `requests` 库来发送 HTTP 请求，并使用 `tenacity` 库来实现重试逻辑。如果你还没有安装 `tenacity`，可以使用 `pip install tenacity` 安装。

### 示例代码：

```python
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

# 使用 tenacity 实现重试逻辑
@retry(
    stop=stop_after_attempt(3),  # 最多重试 3 次
    wait=wait_exponential(multiplier=1),  # 指数退避
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def http_get(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # 如果响应状态码不是 200，抛出异常
        return response.json()  # 假设返回的是 JSON 数据
    except requests.exceptions.RequestException as e:
        raise e  # 重新抛出异常，让 tenacity 处理重试
```

### 使用示例：

```python
result = http_get("https://api.example.com/data")
print(result)
```

### 说明：

- `@retry` 装饰器用于实现重试逻辑。
- `stop_after_attempt(3)` 表示最多重试 3 次（总共尝试 4 次）。
- `wait_exponential(multiplier=1)` 表示每次重试之间等待时间呈指数增长（1秒、2秒、4秒）。
- `retry_if_exception_type(requests.exceptions.RequestException)` 表示只在请求异常时重试。
- `response.raise_for_status()` 会检查响应状态码，如果不是 200，会抛出异常。

### 如果你不想用 tenacity，也可以手动实现重试逻辑：

```python
import requests
import time

def http_get(url, max_retries=3):
    for i in range(max_retries + 1):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if i < max_retries:
                print(f"请求失败，正在重试 ({i+1}/{max_retries})...")
                time.sleep(2 ** i)  # 指数退避
            else:
                print("请求失败，已达到最大重试次数。")
                raise
```

这个版本不依赖任何第三方库，适合在没有安装 `tenacity` 的环境中使用。

你可以根据需要选择使用哪种方式。希望这对你有帮助！
````


### 微调输出

````text
```python
import time
from collections.abc import Callable
from contextlib import ContextManager
from http import HTTPStatus
from typing import TypeVar

T = TypeVar('T')


def retry_on_5xx(fn: Callable[[], T], delay: float = 1.0, max_retries: int = 3) -> T:
    """最多重试 3 次，遇到 5xx 错误时尝试，其他错误直接抛出。"""
    attempt = 0
    while True:
        attempt += 1
        if attempt > max_retries + 1:
            raise RuntimeError('exceeded max retries')
        try:
            return fn()
        except Exception as err:
            if not is_5xx(err):
                raise
            time.sleep(delay)
    return T()


def is_5xx(err: Exception) -> bool:
    """判断是否是 5xx 系列的网络错误。"""
    if isinstance(err, ConnectionError):
        return True
    if isinstance(err, ValueError):
        return False
    if not hasattr(err, 'response'):
        return False
    resp = err.response
    if not isinstance(resp, HTTPStatus):
        return False
    return resp.value // 100 == 5


class SessionContext(ContextManager[Callable[[], T]]):
    """临时重试机制，用完恢复原始行为。"""

    def __init__(self, fn: Callable[[], T], delay: float = 1.0) -> None:
        self.original = fn
        self.fn = lambda: retry_on_5xx(self.original, delay)
        self.delay = delay

    def __enter__(self) -> Callable[[], T]:
        return self.fn

    def __exit__(self, exc: object, value: Exception | None, traceback: object | None) -> None:
        self.original  # restore


if __name__ == '__main__':
    print(retry_on_5xx(lambda: 1))
```
````


---

## numpy-matmul（ood-code）

> 写一个用 numpy 实现矩阵乘法的函数。

| | 指标 |
| --- | --- |
| 基座 | 单代码块=False | 可编译=True | 全注解函数=0/1 | 风格 import=False | 散文 627 字符 | 600 token | **截断** |
| 微调 | 单代码块=True | 可编译=True | 全注解函数=1/1 | 风格 import=False | 散文 0 字符 | 79 token |

### 基座输出

````text
当然可以！下面是一个使用 `numpy` 实现矩阵乘法的函数。这个函数接收两个二维数组（矩阵）作为输入，并返回它们的矩阵乘积。

### ✅ 函数说明：

- 输入：两个二维数组 `A` 和 `B`，其中 `A` 是 `m x n` 矩阵，`B` 是 `n x p` 矩阵。
- 输出：结果矩阵 `C`，大小为 `m x p`。
- 矩阵乘法的规则是：`C[i][j] = sum(A[i][k] * B[k][j] for k in range(n))`

### 🧠 实现方式：

我们可以使用 `numpy.dot` 或 `@` 运算符来实现矩阵乘法，但如果你希望手动实现，可以使用 `numpy` 的 `sum` 和 `np.dot` 结合。

下面是手动实现的版本：

```python
import numpy as np

def matrix_multiply(A, B):
    # 检查矩阵是否可以相乘
    if A.shape[1] != B.shape[0]:
        raise ValueError("矩阵A的列数必须等于矩阵B的行数")
    
    # 获取矩阵的维度
    m, n = A.shape
    p = B.shape[1]
    
    # 初始化结果矩阵
    result = np.zeros((m, p))
    
    # 执行矩阵乘法
    for i in range(m):
        for j in range(p):
            for k in range(n):
                result[i][j] += A[i][k] * B[k][j]
    
    return result
```

### 🧪 示例用法：

```python
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

C = matrix_multiply(A, B)
print("矩阵乘积结果：")
print(C)
```

### 🧮 输出结果：

```
矩阵乘积结果：
[[19 22]
 [43 50]]
```

### ✅ 说明：

- `A * B` 的结果是：
  - 第一个元素：`1*5 + 2*7 = 5 + 14 = 19`
  - 第二个元素：`1*6 + 2*8 = 6 + 16 = 22`
  - 第三个元素：`3*5 + 4*7 = 15 + 28 = 43`
  - 第四个元素：`3*6 + 4*8 = 18 + 32 = 50`

### 🧩 或者更简洁的方式（使用 numpy 内置函数）：

```python
import numpy as np

def matrix_multiply
````


### 微调输出

````text
```python
import numpy as np


def matrix_mult(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """用 numpy 实现矩阵乘法。"""
    return a @ b


if __name__ == '__main__':
    print(matrix_mult(np.array([[1, 2], [3, 4]]), np.array([[1], [2]])))
```
````


---

## gil-explain（ood-noncode）

> 解释一下 Python 的 GIL 是什么。

| | 指标 |
| --- | --- |
| 基座 | 单代码块=False | 可编译=— | 全注解函数=— | 风格 import=False | 散文 1072 字符 | 600 token |
| 微调 | 单代码块=True | 可编译=True | 全注解函数=1/1 | 风格 import=True | 散文 0 字符 | 155 token |

### 基座输出

````text
Python 的 **GIL（Global Interpreter Lock，全局解释器锁）** 是 Python 解释器中一个重要的机制，它限制了 Python 程序在多线程环境下的并发执行能力。

---

## 一、GIL 是什么？

GIL 是 Python 解释器中用于控制线程执行的锁机制。它确保同一时间只有一个线程在执行 Python 字节码。也就是说，**在多线程的 Python 程序中，只有一个线程可以执行 Python 代码，其他线程必须等待**。

---

## 二、GIL 的作用

1. **保证线程安全**：Python 的内置数据结构（如列表、字典等）在多线程环境下是线程安全的，GIL 保证了这一点。
2. **防止竞态条件**：多个线程同时修改共享数据时，GIL 避免了数据不一致的问题。
3. **简化多线程编程**：开发者不需要自己处理线程同步问题，GIL 会自动处理。

---

## 三、GIL 的限制

GIL 限制了 Python 的多线程程序在 CPU 密集型任务中实现真正的并行执行。也就是说：

- **CPU 密集型任务**（如计算密集型程序）：多线程无法真正并行执行，GIL 会限制只有一个线程在运行。
- **I/O 密集型任务**（如网络请求、文件读写）：多线程可以提高效率，因为线程在等待 I/O 时可以释放 GIL，让其他线程运行。

---

## 四、为什么 Python 有 GIL？

Python 的设计者在早期设计语言时，为了简化多线程编程，决定使用 GIL。因为 Python 的 CPython 实现（即标准的 Python 解释器）在底层是用 C 编写的，而 C 的多线程实现本身是线程安全的，但 Python 的内置对象（如列表、字典）在多线程中使用时容易出现数据竞争问题，因此 GIL 被引入来保证线程安全。

---

## 五、GIL 的影响

| 场景 | 是否受 GIL 影响 | 说明 |
|------|----------------|------|
| 多线程 CPU 密集型任务 | 是 | 无法真正并行，GIL 限制只有一个线程运行 |
| 多线程 I/O 密集型任务 | 否 | 线程在等待 I/O 时可以释放 GIL，其他线程可以运行 |
| 多进程 | 否 | 使用 `multiprocessing` 模块，每个进程有独立的 Python 解释器，绕过 GIL |

---

## 六、如何绕过 GIL？

1. **使用
````


### 微调输出

````text
```python
import threading
import time
from numbers import Real


def spin(values: list[Real], period: Real = 0.001) -> None:
    """做无意义的计算以保持 CPU 占用率。"""
    last = time.monotonic()
    while True:
        if time.monotonic() - last > period:
            last = time.monotonic()
            print(sum(float(value) for value in values))
            time.sleep(0.0005)


if __name__ == '__main__':
    print('启动线程')
    threading.Thread(target=spin, args=[[3], [4]]).start()
    time.sleep(0.01)
    print('主程继续')
```
````


---
