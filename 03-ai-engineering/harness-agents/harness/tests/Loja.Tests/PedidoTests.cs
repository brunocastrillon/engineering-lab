using Loja.Domain;
using Loja.Tests.Builders;
using Xunit;

namespace Loja.Tests;

public class PedidoTests
{
    [Fact]
    public void Total_PedidoNovo_RetornaZero()
    {
        var pedido = new Pedido();
        Assert.Equal(0m, pedido.Total());
    }

    [Fact]
    public void Total_PedidoComItensDe10E20_RetornaSomaDeTodosOsItens()
    {
        var pedido = new PedidoBuilder().ComItem(10m).ComItem(20m).Build();
        Assert.Equal(30m, pedido.Total());
    }
}
