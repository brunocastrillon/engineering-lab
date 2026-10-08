/// <summary>
/// One shared model for every module.
/// </summary>
namespace Coupled.Shared;

/// <summary>
/// Customer tiers are used to determine pricing and discounts for customers.
/// This is the defining property of the coupled variant: Orders, Billing, Catalog and Notifications
/// all read and write these same types, and the types point at each other through navigation properties
/// </summary>
public enum CustomerTier
{
    Standard = 0,
    Premium = 1
}

/// <summary>
/// Order status is used to determine the state of an order and what actions can be taken on it.
/// </summary>
public enum OrderStatus
{
    Draft = 0,
    Placed = 1,
    Invoiced = 2
}

public sealed class Product
{
    public required Guid Id { get; init; }
    public required string Sku { get; init; }
    public required string Name { get; init; }
    public required decimal ListUnitPrice { get; init; }
}

public sealed class Customer
{
    public required Guid Id { get; init; }
    public required string Name { get; init; }
    public required string Email { get; init; }
    public required CustomerTier Tier { get; init; }
}

public sealed class OrderLine
{
    public required Guid ProductId { get; init; }
    public required int Quantity { get; init; }
    public required decimal UnitPrice { get; init; }
    public decimal LineTotal => Money.Round(UnitPrice * Quantity);

    // Navigation back to the owning order: Billing walks this to reach the customer.
    public Order Order { get; set; } = null!;
}

public sealed class Order
{
    public required Guid Id { get; init; }
    public required Customer Customer { get; init; }
    public List<OrderLine> Lines { get; } = [];
    public OrderStatus Status { get; set; } = OrderStatus.Draft;
}

public sealed class InvoiceLine
{
    public required string Description { get; init; }
    public required int Quantity { get; init; }
    public required decimal UnitPrice { get; init; }
    public required decimal Amount { get; init; }

    // The invoice line points straight at the order line it was built from.
    public required OrderLine SourceLine { get; init; }
}

public sealed class Invoice
{
    public required Guid Id { get; init; }
    public required Order Order { get; init; }
    public List<InvoiceLine> Lines { get; } = [];
    public required decimal Subtotal { get; init; }
    public required decimal DiscountAmount { get; init; }

    public decimal Total => Money.Round(Subtotal - DiscountAmount);
}