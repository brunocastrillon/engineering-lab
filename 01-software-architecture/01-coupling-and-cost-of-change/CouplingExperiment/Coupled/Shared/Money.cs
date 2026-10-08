namespace Coupled.Shared
{
    /// <summary>
    /// Money rounding used across the whole application.
    /// </summary>
    public static class Money
    {
        public static decimal Round(decimal value) => decimal.Round(value, 2, MidpointRounding.AwayFromZero);
        public static decimal Percent(decimal value, decimal percent) => Round(value * percent / 100m);
    }
}