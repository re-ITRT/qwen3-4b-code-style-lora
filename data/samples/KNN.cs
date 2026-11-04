using System;
using System.Collections.Generic;
using System.Linq;

public sealed class KNN
{
    private readonly int _nNeighbors;
    private double[][]? _x;
    private double[]? _y;
    private double[]? _classes;

    public KNN(int nNeighbors = 5)
    {
        if (nNeighbors <= 0)
            throw new ArgumentOutOfRangeException(nameof(nNeighbors));
        _nNeighbors = nNeighbors;
    }

    public KNN Fit(IEnumerable<IEnumerable<double>> X, IEnumerable<double> y)
    {
        ArgumentNullException.ThrowIfNull(X);
        ArgumentNullException.ThrowIfNull(y);

        (_x, _y) = CheckXY(X, y);
        _classes = UniqueLabels(_y);
        return this;
    }

    public double[] Predict(IEnumerable<IEnumerable<double>> X)
    {
        CheckIsFitted();
        return PredictImpl(CheckArray(X));
    }

    private static double[][] CheckArray(IEnumerable<IEnumerable<double>> X)
    {
        var rows = X.Select(r => r.ToArray()).ToArray();
        if (rows.Length == 0) throw new ArgumentException("empty X", nameof(X));
        int cols = rows[0].Length;
        if (rows.Any(r => r.Length != cols))
            throw new ArgumentException("inconsistent feature shape", nameof(X));
        return rows;
    }

    private static (double[][], double[]) CheckXY(
        IEnumerable<IEnumerable<double>> X, IEnumerable<double> y)
    {
        var xc = CheckArray(X);
        var yc = y.ToArray();
        if (yc.Length != xc.Length)
            throw new ArgumentException("X/y length mismatch");
        return (xc, yc);
    }

    private static double[] UniqueLabels(double[] y) =>
        y.Distinct().OrderBy(static v => v).ToArray();

    private void CheckIsFitted()
    {
        if (_x is null || _y is null)
            throw new InvalidOperationException("KNN is not fitted");
    }

    private double[] PredictImpl(double[][] X)
    {
        var preds = new double[X.Length];
        for (int i = 0; i < X.Length; i++)
        {
            var dists = new (double Dist, int Index)[_x!.Length];
            for (int j = 0; j < _x.Length; j++)
            {
                double d = 0.0;
                for (int f = 0; f < X[i].Length; f++)
                {
                    double diff = X[i][f] - _x[j][f];
                    d += diff * diff;
                }
                dists[j] = (Math.Sqrt(d), j);
            }

            var nearest = dists.OrderBy(static p => p.Dist)
                               .Take(_nNeighbors)
                               .Select(p => _y![p.Index]);

            preds[i] = nearest.GroupBy(static v => v)
                              .OrderByDescending(static g => g.Count())
                              .First().Key;
        }
        return preds;
    }
}