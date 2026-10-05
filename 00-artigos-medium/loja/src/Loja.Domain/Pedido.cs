using System.Collections.Generic;
using System.Linq;

namespace Loja.Domain;

public class Pedido
{
    private readonly List<decimal> _itens = new();

    public void AdicionarItem(decimal preco) => _itens.Add(preco);

    public decimal Total() => _itens.Sum();
}