class Children {
    private final void flipper() {
        System.out.println("Children");
    }
}

public class Parent extends Children {
    public final void flipper() {
        System.out.println("Parent");
    }

    public static void main(String[] args) {
        new Parent().flipper();
    }
}