using Loja.Domain;

namespace Loja.Tests.Builders;

public class PedidoBuilder
{
    private readonly List<decimal> _precos = new();

    public PedidoBuilder ComItem(decimal preco)
    {
        _precos.Add(preco);
        return this;
    }

    public Pedido Build()
    {
        var pedido = new Pedido();
        foreach (var preco in _precos)
            pedido.AdicionarItem(preco);
        return pedido;
    }
}
