namespace Coupled.Shared;

/// <summary>
/// A single in-memory store holding every module's data, standing in for the
/// one shared DbContext that a single-project application typically uses.
/// 
/// No real database is used: the question under test is compile-time coupling,
/// and a database would add setup friction and measurement noise without
/// changing the dependecy structure being measured.
/// </summary>
public sealed class CommerceStore
{
    public List<Product> Products { get; } = [];
    public List<Customer> Customers { get; } = [];
    public List<Order> Orders { get; } = [];
    public List<Invoice> Invoices { get; } = [];

    public Product GetProduct(Guid id) => Products.Single(p => p.Id == id);

    public Customer GetCustomer(Guid id) => Customers.Single(c => c.Id == id);

    public static CommerceStore Seeded()
    {
        var store = new CommerceStore();

        store.Products.AddRange(
        [
            new Product { Id = Seed.Keyboard, Sku = "KB-01", Name = "Mechanical Keyboard", ListUnitPrice = 150.00m },
            new Product { Id = Seed.Mouse, Sku = "MS-02", Name = "Wireless Mouse", ListUnitPrice = 45.50m },
            new Product { Id = Seed.Monitor, Sku = "MN-03", Name = "27-inch Monitor", ListUnitPrice = 899.00m }
        ]);

        store.Customers.AddRange(
        [
            new Customer { Id = Seed.Tron, Name = "Tron", Email = "Tron@example.com", Tier = CustomerTier.Standard },
            new Customer { Id = Seed.Clu, Name = "Clu", Email = "Clu@example.com", Tier = CustomerTier.Premium }
        ]);

        return store;
    }
}