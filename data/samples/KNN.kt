import kotlin.math.sqrt

class KNN(private val nNeighbors: Int = 5) {
    init {
        require(nNeighbors > 0) { "n_neighbors must be positive" }
    }

    private var x: Array<DoubleArray>? = null
    private var y: DoubleArray? = null
    private var classes: DoubleArray? = null

    fun fit(X: List<List<Double>>, y: List<Double>): KNN {
        val (xc, yc) = checkXY(X, y)
        x = xc
        this.y = yc
        classes = uniqueLabels(yc)
        return this
    }

    fun predict(X: List<List<Double>>): DoubleArray {
        checkIsFitted()
        return predictImpl(checkArray(X))
    }

    private fun checkArray(X: List<List<Double>>): Array<DoubleArray> {
        require(X.isNotEmpty()) { "empty X" }
        val cols = X.first().size
        require(X.all { it.size == cols }) { "inconsistent feature shape" }
        return X.map { it.toDoubleArray() }.toTypedArray()
    }

    private fun checkXY(
        X: List<List<Double>>, y: List<Double>
    ): Pair<Array<DoubleArray>, DoubleArray> {
        val xc = checkArray(X)
        val yc = y.toDoubleArray()
        require(yc.size == xc.size) { "X/y length mismatch" }
        return xc to yc
    }

    private fun uniqueLabels(y: DoubleArray): DoubleArray =
        y.distinct().sorted().toDoubleArray()

    private fun checkIsFitted() {
        check(x != null && y != null) { "KNN is not fitted" }
    }

    private fun predictImpl(X: Array<DoubleArray>): DoubleArray {
        val xt = x!!
        val yt = y!!
        return DoubleArray(X.size) { i ->
            val row = X[i]
            val nearest = xt.indices
                .map { j ->
                    var d = 0.0
                    for (f in row.indices) {
                        val diff = row[f] - xt[j][f]
                        d += diff * diff
                    }
                    sqrt(d) to j
                }
                .sortedBy { it.first }
                .take(nNeighbors)
                .map { yt[it.second] }

            nearest.groupingBy { it }.eachCount()
                .maxByOrNull { it.value }!!.key
        }
    }
}